"""
ui/dialogs_clientes.py — Formulario de alta y edición de clientes.

Responsabilidades:
  - DialogoFormularioCliente: formulario compartido para crear y editar.
  - Validación inline: errores junto al campo, sin QMessageBox por campo.
  - Persistencia vía db/queries_clientes.py.

Reglas arquitectónicas:
  - Sin SQL inline.
  - Sin imports de otros módulos UI (evita circulares).
  - Colores desde ui/theme.py.
"""
import re

from ui.core.modal import DialogoModalIntegrado
from ui.core.modal import ModalOverlay, ModalResult
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFrame, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt

from ui.core.theme import (
    COLOR_PRIMARY, COLOR_BG, COLOR_CARD_BG, COLOR_TEXT_MAIN,
    COLOR_TEXT_SEC, COLOR_BORDER, COLOR_DANGER
)
from db import queries_clientes as qc


# ── Constantes de dominio ─────────────────────────────────────────────────────

CONDICIONES_IVA = [
    "Consumidor Final",
    "Responsable Inscripto",
    "Monotributista",
    "Exento",
    "No Responsable",
]

# CUIT argentino: XX-XXXXXXXX-X (con guiones obligatorios)
_RE_CUIT  = re.compile(r"^\d{2}-\d{7,8}-\d{1}$")
_RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_RE_TEL   = re.compile(r"^[0-9+\-\(\)\s]+$")

# ── Estilos de campos ─────────────────────────────────────────────────────────

_INPUT_NORMAL = (
    f"border: 1px solid {COLOR_BORDER}; border-radius: 6px; "
    f"padding: 7px 10px; background-color: {COLOR_CARD_BG}; "
    f"color: {COLOR_TEXT_MAIN}; font-size: 13px;"
)
_INPUT_ERROR = (
    f"border: 1.5px solid {COLOR_DANGER}; border-radius: 6px; "
    f"padding: 7px 10px; background-color: #fff5f5; "
    f"color: {COLOR_TEXT_MAIN}; font-size: 13px;"
)

# ══════════════════════════════════════════════════════════════════════════════
# COMPONENTES INTERNOS
# ══════════════════════════════════════════════════════════════════════════════

class _CampoFormulario(QFrame):
    """
    Contenedor de un campo del formulario con etiqueta y mensaje de error inline.

    Uso:
        campo = _CampoFormulario("Nombre", QLineEdit(), requerido=True)
        campo.set_error("Campo obligatorio")
        campo.clear_error()
        valor = campo.widget.text()
    """

    def __init__(self, etiqueta: str, widget, requerido: bool = False):
        super().__init__()
        self.setObjectName("campo_formulario")
        self.setStyleSheet("_CampoFormulario#campo_formulario { border: none; background: transparent; }")
        ly = QVBoxLayout(self)
        ly.setContentsMargins(0, 0, 0, 0)
        ly.setSpacing(4)

        # Etiqueta con asterisco para campos obligatorios
        texto_lbl = (
            f"{etiqueta} <span style='color:{COLOR_DANGER};'>*</span>"
            if requerido else etiqueta
        )
        lbl = QLabel(texto_lbl)
        lbl.setStyleSheet(
            f"color: {COLOR_TEXT_SEC}; font-size: 12px; font-weight: 600; border: none;"
        )

        # Aplicar estilo base al widget
        self.widget = widget
        if isinstance(widget, QLineEdit):
            widget.setStyleSheet(_INPUT_NORMAL)
            widget.setMinimumHeight(36)
        elif isinstance(widget, QComboBox):
            widget.setMinimumHeight(36)
            # No aplicamos estilos manuales ni vistas, usamos el QComboBox nativo 
            # para que herede exactamente el mismo estilo global que el combobox de Unidad en Stock

        # Error label (oculto por defecto)
        self._lbl_error = QLabel("")
        self._lbl_error.setStyleSheet(
            f"color: {COLOR_DANGER}; font-size: 11px; border: none;"
        )
        self._lbl_error.setVisible(False)

        ly.addWidget(lbl)
        ly.addWidget(self.widget)
        ly.addWidget(self._lbl_error)

    def set_error(self, msg: str):
        self._lbl_error.setText(msg)
        self._lbl_error.setVisible(bool(msg))
        if isinstance(self.widget, QLineEdit):
            self.widget.setStyleSheet(_INPUT_ERROR if msg else _INPUT_NORMAL)

    def clear_error(self):
        self.set_error("")

    def tiene_error(self) -> bool:
        return self._lbl_error.isVisible()


def _separador_seccion(titulo: str) -> QFrame:
    """Crea un separador visual con título de sección en mayúsculas."""
    frame = QFrame()
    frame.setStyleSheet("border: none;")
    ly = QVBoxLayout(frame)
    ly.setContentsMargins(0, 14, 0, 6)
    ly.setSpacing(0)

    lbl = QLabel(titulo.upper())
    lbl.setStyleSheet(
        f"color: {COLOR_TEXT_SEC}; font-size: 10px; font-weight: 800; "
        f"letter-spacing: 1px; border: none; padding-bottom: 4px;"
    )
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.HLine)
    sep.setStyleSheet(
        f"background-color: {COLOR_BORDER}; max-height: 1px; border: none;"
    )
    ly.addWidget(lbl)
    ly.addWidget(sep)
    return frame


# ══════════════════════════════════════════════════════════════════════════════
# DIÁLOGO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class DialogoFormularioCliente(DialogoModalIntegrado):
    """
    Formulario compartido para crear o editar un cliente, ahora integrado como QFrame.

    Crear:  DialogoFormularioCliente(conn, parent=parent)
    Editar: DialogoFormularioCliente(conn, id_cliente=X, parent=parent)

    Después de accept():
        self.id_guardado  →  int con el id_cliente persistido
    """

    def __init__(self, conn, id_cliente: int | None = None, parent=None):
        super().__init__(parent)
        self.conn            = conn
        self._id_cliente     = id_cliente
        self._modo_edicion   = id_cliente is not None
        self.id_guardado: int | None = None
        self._modal_parent   = None

        self.setMinimumWidth(500)
        self.setMaximumWidth(620)
        
        self.setObjectName("formulario_cliente_card")
        self.setStyleSheet(f"""
            QFrame#formulario_cliente_card {{
                background-color: {COLOR_CARD_BG};
                border-radius: 12px;
                border: 1px solid {COLOR_BORDER};
            }}
        """)

        # Mapa nombre → _CampoFormulario, para acceso directo en validación
        self._campos: dict[str, _CampoFormulario] = {}

        self._construir_ui()
        if self._modo_edicion:
            self._precargar()

    # ──────────────────────────────────────────────────────────────────────────
    # CONSTRUCCIÓN DE LA UI
    # ──────────────────────────────────────────────────────────────────────────

    def _construir_ui(self):
        ly = QVBoxLayout(self)
        ly.setContentsMargins(24, 20, 24, 20)
        ly.setSpacing(16)

        # Encabezado interno
        lbl_titulo = QLabel(
            f"Editar: {self._det['nombre']}" if self._modo_edicion else "Nuevo Cliente"
        )
        lbl_titulo.setStyleSheet(
            f"font-size: 18px; font-weight: 900; color: {COLOR_TEXT_MAIN};"
        )
        lbl_sub = QLabel(
            "Modificá los campos y guardá los cambios."
            if self._modo_edicion
            else "Complete los datos del cliente. Los campos marcados con * son obligatorios."
        )
        lbl_sub.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SEC};")
        lbl_sub.setWordWrap(True)
        ly.addWidget(lbl_titulo)
        ly.addSpacing(2)
        ly.addWidget(lbl_sub)

        # ── Sección 1: Datos Generales ────────────────────────────────────
        ly.addWidget(_separador_seccion("Datos Generales"))

        inp_nombre = QLineEdit()
        inp_nombre.setPlaceholderText("Nombre completo o razón social")
        campo_nombre = _CampoFormulario(
            "Nombre / Razón Social", inp_nombre, requerido=True
        )
        self._campos["nombre_completo"] = campo_nombre
        ly.addWidget(campo_nombre)
        ly.addSpacing(6)

        inp_cuit = QLineEdit()
        inp_cuit.setPlaceholderText("Ej: 20-12345678-9 (CUIT) o 12345678 (DNI)")
        inp_cuit.setMaxLength(13)
        campo_cuit = _CampoFormulario("CUIT / DNI", inp_cuit)
        self._campos["cuit_dni"] = campo_cuit
        ly.addWidget(campo_cuit)

        # ── Sección 2: Datos de Contacto ──────────────────────────────────
        ly.addWidget(_separador_seccion("Datos de Contacto"))

        fila_tel_email = QHBoxLayout()
        fila_tel_email.setSpacing(12)

        inp_tel = QLineEdit()
        inp_tel.setPlaceholderText("Ej: 3512001122")
        campo_tel = _CampoFormulario("Teléfono", inp_tel)
        self._campos["telefono"] = campo_tel

        inp_email = QLineEdit()
        inp_email.setPlaceholderText("correo@ejemplo.com")
        campo_email = _CampoFormulario("Email", inp_email)
        self._campos["email"] = campo_email

        fila_tel_email.addWidget(campo_tel, stretch=1)
        fila_tel_email.addWidget(campo_email, stretch=2)
        ly.addLayout(fila_tel_email)
        ly.addSpacing(6)

        fila_loc = QHBoxLayout()
        fila_loc.setSpacing(12)

        inp_ciudad = QLineEdit()
        inp_ciudad.setPlaceholderText("Ciudad")
        campo_ciudad = _CampoFormulario("Ciudad", inp_ciudad)
        self._campos["ciudad"] = campo_ciudad

        inp_dir = QLineEdit()
        inp_dir.setPlaceholderText("Calle, número, piso...")
        campo_dir = _CampoFormulario("Dirección", inp_dir)
        self._campos["direccion"] = campo_dir

        fila_loc.addWidget(campo_ciudad, stretch=1)
        fila_loc.addWidget(campo_dir, stretch=2)
        ly.addLayout(fila_loc)

        # ── Sección 3: Información Comercial ──────────────────────────────
        ly.addWidget(_separador_seccion("Información Comercial"))

        combo_iva = QComboBox()
        combo_iva.addItems(CONDICIONES_IVA)

        campo_iva = _CampoFormulario("Condición IVA", combo_iva)
        self._campos["condicion_iva"] = campo_iva
        ly.addWidget(campo_iva)

        # ── Error global ──────────────────────────────────────────────────
        self._lbl_error_global = QLabel("")
        self._lbl_error_global.setStyleSheet(
            f"color: {COLOR_DANGER}; font-size: 12px; "
            f"background-color: #fff5f5; border: 1px solid {COLOR_DANGER}; "
            f"border-radius: 6px; padding: 8px;"
        )
        self._lbl_error_global.setWordWrap(True)
        self._lbl_error_global.setVisible(False)
        ly.addSpacing(10)
        ly.addWidget(self._lbl_error_global)

        # ── Separador y botones ───────────────────────────────────────────
        ly.addSpacing(14)
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(
            f"background-color: {COLOR_BORDER}; max-height: 1px; border: none;"
        )
        ly.addWidget(sep)
        ly.addSpacing(14)

        ly_btns = QHBoxLayout()
        ly_btns.setSpacing(8)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet(
            f"background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_MAIN}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 6px; "
            f"font-weight: 600; font-size: 13px; padding: 9px 18px;"
        )
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)
        btn_cancelar.setShortcut("Escape")

        self._btn_guardar = QPushButton(
            "Guardar Cambios" if self._modo_edicion else "Crear Cliente"
        )
        self._btn_guardar.setStyleSheet(
            f"background-color: {COLOR_PRIMARY}; color: white; border: none; "
            f"border-radius: 6px; font-weight: 700; font-size: 13px; "
            f"padding: 9px 22px;"
        )
        self._btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_guardar.clicked.connect(self._guardar)
        self._btn_guardar.setDefault(True)

        ly_btns.addStretch()
        ly_btns.addWidget(btn_cancelar)
        ly_btns.addWidget(self._btn_guardar)
        ly.addLayout(ly_btns)

    # ──────────────────────────────────────────────────────────────────────────
    # PRE-CARGA EN MODO EDICIÓN
    # ──────────────────────────────────────────────────────────────────────────

    def _precargar(self):
        """Rellena el formulario con los datos actuales del cliente."""
        det = qc.obtener_detalle_cliente(self.conn, self._id_cliente)
        if det is None:
            return

        def _set_texto(key: str, valor: str | None):
            campo = self._campos.get(key)
            if campo and isinstance(campo.widget, QLineEdit):
                campo.widget.setText(valor or "")

        _set_texto("nombre_completo", det["nombre"])
        _set_texto("cuit_dni",        det["cuit_dni"])
        _set_texto("telefono",        det["telefono"])
        _set_texto("email",           det["email"])
        _set_texto("ciudad",          det["ciudad"])
        _set_texto("direccion",       det["direccion"])

        combo = self._campos["condicion_iva"].widget
        idx = combo.findText(det["condicion_iva"])
        if idx >= 0:
            combo.setCurrentIndex(idx)

    # ──────────────────────────────────────────────────────────────────────────
    # VALIDACIÓN
    # ──────────────────────────────────────────────────────────────────────────

    def _txt(self, key: str) -> str:
        campo = self._campos.get(key)
        if campo and isinstance(campo.widget, QLineEdit):
            return campo.widget.text().strip()
        return ""

    def _validar(self) -> bool:
        """
        Valida todos los campos.
        Muestra mensajes de error inline junto a cada campo.
        Retorna True si el formulario es válido.
        """
        # Limpiar errores anteriores
        for campo in self._campos.values():
            campo.clear_error()
        self._lbl_error_global.setVisible(False)

        hay_error = False

        # Nombre: obligatorio
        if not self._txt("nombre_completo"):
            self._campos["nombre_completo"].set_error("Este campo es obligatorio.")
            hay_error = True

        # CUIT: opcional, pero si se ingresó debe tener formato válido
        cuit = self._txt("cuit_dni")
        if cuit and not _RE_CUIT.match(cuit):
            self._campos["cuit_dni"].set_error(
                "Formato de CUIT inválido. Ejemplo: 20-12345678-9"
            )
            hay_error = True

        # Email: opcional, pero si se ingresó debe tener formato válido
        email = self._txt("email")
        if email and not _RE_EMAIL.match(email):
            self._campos["email"].set_error(
                "Email inválido. Ejemplo: nombre@dominio.com"
            )
            hay_error = True

        # Teléfono: opcional, pero si se ingresó debe ser un valor numérico/formato válido
        tel = self._txt("telefono")
        if tel and not _RE_TEL.match(tel):
            self._campos["telefono"].set_error(
                "Solo se aceptan números y los caracteres: + - ( ) espacios"
            )
            hay_error = True

        # Enfocar primer campo con error
        if hay_error:
            for campo in self._campos.values():
                if campo.tiene_error() and isinstance(campo.widget, QLineEdit):
                    campo.widget.setFocus()
                    campo.widget.selectAll()
                    break

        return not hay_error

    def _recoger_datos(self) -> dict:
        combo = self._campos["condicion_iva"].widget
        return {
            "nombre_completo": self._txt("nombre_completo"),
            "cuit_dni":        self._txt("cuit_dni") or None,
            "telefono":        self._txt("telefono") or None,
            "email":           self._txt("email") or None,
            "ciudad":          self._txt("ciudad") or None,
            "direccion":       self._txt("direccion") or None,
            "condicion_iva":   combo.currentText(),
            "activo":          1,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # GUARDADO
    # ──────────────────────────────────────────────────────────────────────────

    def _guardar(self):
        if not self._validar():
            return

        datos = self._recoger_datos()
        self._btn_guardar.setEnabled(False)
        try:
            if self._modo_edicion:
                ok = qc.actualizar_cliente(self.conn, self._id_cliente, datos)
                if ok:
                    self.id_guardado = self._id_cliente
                    self.accept()
                else:
                    self._mostrar_error_global(
                        "No se pudo actualizar el cliente. Intente nuevamente."
                    )
            else:
                self.id_guardado = qc.guardar_cliente(self.conn, datos)
                if self.id_guardado:
                    self.accept()
                else:
                    self._mostrar_error_global(
                        "No se pudo guardar el cliente. Intente nuevamente."
                    )
        except Exception as e:
            msg = str(e)
            if "UNIQUE" in msg.upper() or "unique" in msg:
                if "cuit_dni" in msg:
                    self._campos["cuit_dni"].set_error(
                        "Este CUIT/DNI ya está registrado en otro cliente."
                    )
                    self._campos["cuit_dni"].widget.setFocus()
                elif "nombre" in msg:
                    self._campos["nombre_completo"].set_error(
                        "Ya existe un cliente con ese nombre."
                    )
                    self._campos["nombre_completo"].widget.setFocus()
                else:
                    self._mostrar_error_global("El dato ingresado ya existe en otro cliente.")
            else:
                self._mostrar_error_global(f"Error al guardar: {msg}")
        finally:
            self._btn_guardar.setEnabled(True)

    def _mostrar_error_global(self, msg: str):
        self._lbl_error_global.setText(f"⚠  {msg}")
        self._lbl_error_global.setVisible(True)

    def set_modal_parent(self, modal):
        self._modal_parent = modal
