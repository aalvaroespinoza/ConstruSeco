"""
ui/clientes.py — Pestaña Clientes de ConstruSeco Pereyra.

Responsabilidades:
  - Encabezado con buscador y acciones (+ Nuevo Cliente)
  - Cinco tarjetas de métricas calculadas en tiempo real
  - Tabla paginada de clientes con selección por fila
  - Panel lateral con detalle del cliente seleccionado
  - CRUD completo: crear, editar, desactivar/reactivar, eliminar
  - Menú de tres puntos (⋯) para acciones secundarias
  - Atajos: F2 (buscador), Ctrl+N (nuevo cliente)

Reglas arquitectónicas:
  - Sin SQL inline: toda consulta pasa por db/queries_clientes.py
  - Sin DDL: toda migración vive en db/conexion.py
  - Colores importados de ui/theme.py
  - Solo importa de db/ y ui/theme.py (sin circulares con otros módulos UI)
  - dialogs_clientes importa solo de db/ y ui/theme.py → seguro importar aquí
"""

from PyQt6.QtWidgets import ( QDialog,

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSplitter, QScrollArea, QComboBox,
    QStackedWidget, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QColor, QAction, QKeySequence

from ui.theme import (
    COLOR_PRIMARY, COLOR_BG, COLOR_CARD_BG, COLOR_TEXT_MAIN,
    COLOR_TEXT_SEC, COLOR_BORDER, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER
)
from ui.dialogs_contactos_notas import DialogoNota

from ui.dialogs_historial import DialogoHistorialCliente
from ui.modal import ModalOverlay, ModalResult
from db import queries_clientes as qc


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS DE FORMATO
# ══════════════════════════════════════════════════════════════════════════════

def _fmt_moneda(valor: float) -> str:
    """Formatea como moneda argentina: $ 1.234,56"""
    return f"$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _iniciales(nombre: str) -> str:
    """Extrae hasta 2 iniciales del nombre para el avatar."""
    partes = [p for p in nombre.strip().split() if p]
    if len(partes) >= 2:
        return (partes[0][0] + partes[1][0]).upper()
    elif partes:
        return partes[0][:2].upper()
    return "?"


# ══════════════════════════════════════════════════════════════════════════════
# TARJETA DE MÉTRICA
# ══════════════════════════════════════════════════════════════════════════════

class _TarjetaMetrica(QFrame):
    def __init__(self, titulo: str, valor: str = "—", color_borde: str = COLOR_PRIMARY):
        super().__init__()
        self.setStyleSheet(f"""
            _TarjetaMetrica {{
                background-color: {COLOR_CARD_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                border-left: 4px solid {color_borde};
            }}
        """)
        self.setMinimumWidth(150)
        self.setFixedHeight(80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(3)

        self._lbl_titulo = QLabel(titulo)
        self._lbl_titulo.setStyleSheet(
            f"color: {COLOR_TEXT_SEC}; font-size: 12px; font-weight: 600; border: none;"
        )
        self._lbl_valor = QLabel(valor)
        self._lbl_valor.setStyleSheet(
            f"color: {COLOR_TEXT_MAIN}; font-size: 20px; font-weight: 900; "
            f"letter-spacing: -0.5px; border: none;"
        )
        layout.addWidget(self._lbl_titulo)
        layout.addWidget(self._lbl_valor)

    def set_valor(self, valor: str):
        self._lbl_valor.setText(valor)


# ══════════════════════════════════════════════════════════════════════════════
# PANEL LATERAL — ESTADO VACÍO
# ══════════════════════════════════════════════════════════════════════════════

class _PanelVacio(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            f"background-color: {COLOR_CARD_BG}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 8px;"
        )
        ly = QVBoxLayout(self)
        ly.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icono = QLabel("👤")
        icono.setStyleSheet("font-size: 42px; border: none;")
        icono.setAlignment(Qt.AlignmentFlag.AlignCenter)

        titulo = QLabel("Seleccioná un cliente")
        titulo.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {COLOR_TEXT_MAIN}; border: none;"
        )
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("Hacé clic en una fila de la tabla\npara ver el detalle aquí.")
        sub.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SEC}; border: none;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ly.addStretch()
        ly.addWidget(icono)
        ly.addSpacing(8)
        ly.addWidget(titulo)
        ly.addSpacing(4)
        ly.addWidget(sub)
        ly.addStretch()


# ══════════════════════════════════════════════════════════════════════════════
# PANEL LATERAL — COMPONENTES
# ══════════════════════════════════════════════════════════════════════════════

class _FilaDetalle(QFrame):
    def __init__(self, etiqueta: str, valor: str = "—"):
        super().__init__()
        self.setStyleSheet("border: none;")
        ly = QHBoxLayout(self)
        ly.setContentsMargins(0, 2, 0, 2)
        ly.setSpacing(8)

        lbl_e = QLabel(etiqueta)
        lbl_e.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 12px; border: none;")
        lbl_e.setFixedWidth(100)
        lbl_e.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self._lbl_v = QLabel(valor)
        self._lbl_v.setStyleSheet(
            f"color: {COLOR_TEXT_MAIN}; font-size: 12px; font-weight: 600; border: none;"
        )
        self._lbl_v.setWordWrap(True)

        ly.addWidget(lbl_e)
        ly.addWidget(self._lbl_v, stretch=1)

    def set_valor(self, valor: str):
        self._lbl_v.setText(valor or "—")


class _SeccionPanel(QFrame):
    def __init__(self, titulo: str):
        super().__init__()
        self.setStyleSheet("border: none;")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 8, 0, 4)
        self._layout.setSpacing(0)

        lbl_tit = QLabel(titulo.upper())
        lbl_tit.setStyleSheet(
            f"color: {COLOR_TEXT_SEC}; font-size: 10px; font-weight: 800; "
            f"letter-spacing: 1px; border: none; padding-bottom: 4px;"
        )
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(
            f"background-color: {COLOR_BORDER}; max-height: 1px; border: none;"
        )
        self._layout.addWidget(lbl_tit)
        self._layout.addWidget(sep)
        self._layout.addSpacing(4)

    def agregar(self, widget):
        self._layout.addWidget(widget)


# ══════════════════════════════════════════════════════════════════════════════
# PANEL LATERAL — DETALLE DEL CLIENTE
# ══════════════════════════════════════════════════════════════════════════════

class _PanelDetalle(QScrollArea):
    """
    Panel lateral con detalle completo del cliente seleccionado.

    Señales emitidas hacia PestanaClientes:
        editar_solicitado(id_cliente)
        desactivar_solicitado(id_cliente)
        eliminar_solicitado(id_cliente)
    """

    editar_solicitado     = pyqtSignal(int)
    desactivar_solicitado = pyqtSignal(int)
    eliminar_solicitado   = pyqtSignal(int)
    recargar_solicitado   = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(
            f"QScrollArea {{ border: none; background-color: {COLOR_CARD_BG}; }}"
        )
        self._id_actual: int | None = None
        self._activo_actual: bool   = True   # estado activo del cliente visible

        self._contenido = QWidget()
        self._contenido.setStyleSheet(
            f"background-color: {COLOR_CARD_BG}; border: none;"
        )
        self._layout = QVBoxLayout(self._contenido)
        self._layout.setContentsMargins(14, 14, 14, 14)
        self._layout.setSpacing(0)
        self.setWidget(self._contenido)

        self._construir()

    # ──────────────────────────────────────────────────────────────────────────
    # CONSTRUCCIÓN
    # ──────────────────────────────────────────────────────────────────────────

    def _construir(self):
        # ── Cabecera ──────────────────────────────────────────────────────
        cabecera = QFrame()
        cabecera.setStyleSheet(
            f"background-color: {COLOR_BG}; border-radius: 8px; "
            f"border: 1px solid {COLOR_BORDER};"
        )
        ly_cab = QVBoxLayout(cabecera)
        ly_cab.setContentsMargins(12, 10, 12, 12)
        ly_cab.setSpacing(6)

        # Fila superior: Avatar + info + botón ⋯
        fila_av = QHBoxLayout()
        fila_av.setSpacing(8)

        self._avatar = QLabel("?")
        self._avatar.setFixedSize(44, 44)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setStyleSheet(
            f"background-color: {COLOR_PRIMARY}; color: white; border-radius: 22px; "
            f"font-size: 16px; font-weight: 800; border: none;"
        )

        info_av = QVBoxLayout()
        info_av.setSpacing(2)
        self._lbl_nombre = QLabel("—")
        self._lbl_nombre.setStyleSheet(
            f"font-weight: 800; font-size: 14px; color: {COLOR_TEXT_MAIN}; border: none;"
        )
        self._lbl_nombre.setWordWrap(True)
        self._lbl_codigo = QLabel("—")
        self._lbl_codigo.setStyleSheet(
            f"font-size: 11px; color: {COLOR_TEXT_SEC}; border: none;"
        )
        info_av.addWidget(self._lbl_nombre)
        info_av.addWidget(self._lbl_codigo)

        # Botón de menú de acciones (⋯)
        self._btn_menu = QPushButton("⋯")
        self._btn_menu.setFixedSize(30, 30)
        self._btn_menu.setStyleSheet(
            f"QPushButton {{ background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_SEC}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 15px; "
            f"font-size: 16px; font-weight: 900; }}"
            f"QPushButton:hover {{ background-color: {COLOR_BG}; color: {COLOR_TEXT_MAIN}; }}"
        )
        self._btn_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_menu.setEnabled(False)
        self._btn_menu.clicked.connect(self._mostrar_menu_acciones)

        fila_av.addWidget(self._avatar)
        fila_av.addLayout(info_av, stretch=1)
        fila_av.addWidget(self._btn_menu, alignment=Qt.AlignmentFlag.AlignTop)

        # Badge de estado
        self._badge_estado = QLabel("ACTIVO")
        self._badge_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge_estado.setFixedHeight(22)
        self._badge_estado.setStyleSheet(
            "background-color: #d1fae5; color: #065f46; border-radius: 10px; "
            "font-size: 10px; font-weight: 700; padding: 0 10px; border: none;"
        )

        # Mini métricas
        fila_mk = QHBoxLayout()
        fila_mk.setSpacing(6)
        self._mk_compras = self._mini_metrica("Compras", "0")
        self._mk_total   = self._mini_metrica("Total", "$0")
        self._mk_ticket  = self._mini_metrica("Ticket Prom.", "$0")
        fila_mk.addWidget(self._mk_compras)
        fila_mk.addWidget(self._mk_total)
        fila_mk.addWidget(self._mk_ticket)

        ly_cab.addLayout(fila_av)
        ly_cab.addWidget(self._badge_estado, alignment=Qt.AlignmentFlag.AlignLeft)
        ly_cab.addSpacing(6)
        ly_cab.addLayout(fila_mk)

        self._layout.addWidget(cabecera)

        # ── Información General ───────────────────────────────────────────
        sec_gral = _SeccionPanel("Información General")
        self._f_cuit  = _FilaDetalle("CUIT / DNI")
        self._f_email = _FilaDetalle("Email")
        self._f_tel   = _FilaDetalle("Teléfono")
        self._f_dir   = _FilaDetalle("Dirección")
        self._f_ciu   = _FilaDetalle("Ciudad")
        for w in (self._f_cuit, self._f_email, self._f_tel, self._f_dir, self._f_ciu):
            sec_gral.agregar(w)
        self._layout.addWidget(sec_gral)

        # ── Información Comercial ─────────────────────────────────────────
        sec_com = _SeccionPanel("Información Comercial")
        self._f_iva      = _FilaDetalle("Condición IVA")
        self._f_ult_comp = _FilaDetalle("Última compra")
        self._f_pres_act = _FilaDetalle("Presupuestos")
        nota_saldo = QLabel(
            "💡 Saldo y cuenta corriente disponibles cuando se implemente el módulo de pagos."
        )
        nota_saldo.setWordWrap(True)
        nota_saldo.setStyleSheet(
            f"color: {COLOR_TEXT_SEC}; font-size: 11px; border: none; "
            f"background-color: {COLOR_BG}; border-radius: 4px; padding: 6px;"
        )
        for w in (self._f_iva, self._f_ult_comp, self._f_pres_act):
            sec_com.agregar(w)
        sec_com.agregar(nota_saldo)
        self._layout.addWidget(sec_com)

        # (Sección Contactos eliminada por requerimiento)

        # ── Notas ─────────────────────────────────────────────────────────
        self._sec_notas = _SeccionPanel("Notas")
        ly_hdr_n = QHBoxLayout()
        ly_hdr_n.setContentsMargins(0, 0, 0, 0)
        lbl_n = QLabel("NOTAS")
        lbl_n.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 10px; font-weight: 800; letter-spacing: 1px; border: none;")
        self._btn_add_nota = QPushButton("+ Nueva Nota")
        self._btn_add_nota.setStyleSheet(f"color: {COLOR_PRIMARY}; font-size: 10px; font-weight: bold; border: none;")
        self._btn_add_nota.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_add_nota.clicked.connect(self._on_add_nota)
        ly_hdr_n.addWidget(lbl_n)
        ly_hdr_n.addStretch()
        ly_hdr_n.addWidget(self._btn_add_nota)
        self._sec_notas._layout.itemAt(0).widget().deleteLater()
        w_hdr_n = QWidget()
        w_hdr_n.setLayout(ly_hdr_n)
        w_hdr_n.setStyleSheet("border: none;")
        self._sec_notas._layout.insertWidget(0, w_hdr_n)

        self._ly_notas = QVBoxLayout()
        self._ly_notas.setSpacing(3)
        self._sec_notas._layout.addLayout(self._ly_notas)
        self._layout.addWidget(self._sec_notas)

        # ── Actividad Reciente ────────────────────────────────────────────
        self._sec_act = _SeccionPanel("Actividad Reciente")
        self._ly_actividad = QVBoxLayout()
        self._ly_actividad.setSpacing(3)
        self._sec_act._layout.addLayout(self._ly_actividad)
        self._layout.addWidget(self._sec_act)

        # ── Botón principal: Editar ───────────────────────────────────────
        self._layout.addSpacing(14)
        self._btn_editar = QPushButton("✏  Editar cliente")
        self._btn_editar.setStyleSheet(
            f"background-color: {COLOR_PRIMARY}; color: white; border-radius: 6px; "
            f"font-weight: bold; font-size: 13px; padding: 9px 14px; border: none;"
        )
        self._btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_editar.setEnabled(False)
        self._btn_editar.clicked.connect(
            lambda: self.editar_solicitado.emit(self._id_actual)
            if self._id_actual is not None else None
        )

        self._btn_historial = QPushButton("📋  Ver historial completo")
        self._btn_historial.setStyleSheet(
            f"background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_MAIN}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 6px; "
            f"font-weight: 600; font-size: 13px; padding: 9px 14px;"
        )
        self._btn_historial.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_historial.setEnabled(False)
        self._btn_historial.clicked.connect(self._on_ver_historial)

        self._layout.addWidget(self._btn_editar)
        self._layout.addSpacing(6)
        self._layout.addWidget(self._btn_historial)
        self._layout.addStretch()

    def _mini_metrica(self, label: str, valor: str) -> QFrame:
        f = QFrame()
        f.setStyleSheet(
            f"background-color: {COLOR_BG}; border-radius: 6px; border: 1px solid {COLOR_BORDER};"
        )
        ly = QVBoxLayout(f)
        ly.setContentsMargins(8, 6, 8, 6)
        ly.setSpacing(2)
        lbl_l = QLabel(label)
        lbl_l.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 10px; border: none;")
        lbl_v = QLabel(valor)
        lbl_v.setStyleSheet(
            f"color: {COLOR_TEXT_MAIN}; font-size: 13px; font-weight: 800; border: none;"
        )
        ly.addWidget(lbl_l)
        ly.addWidget(lbl_v)
        return f

    def _set_mini(self, frame: QFrame, valor: str):
        labels = frame.findChildren(QLabel)
        if len(labels) >= 2:
            labels[1].setText(valor)

    # ──────────────────────────────────────────────────────────────────────────
    # MENÚ DE TRES PUNTOS
    # ──────────────────────────────────────────────────────────────────────────

    def _mostrar_menu_acciones(self):
        if self._id_actual is None:
            return

        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; "
            f"border-radius: 6px; padding: 4px; }}"
            f"QMenu::item {{ padding: 8px 20px; border-radius: 4px; "
            f"color: {COLOR_TEXT_MAIN}; font-size: 13px; }}"
            f"QMenu::item:selected {{ background-color: {COLOR_BG}; }}"
            f"QMenu::separator {{ height: 1px; background-color: {COLOR_BORDER}; margin: 3px 8px; }}"
        )

        act_editar = QAction("✏   Editar cliente", self)
        act_editar.triggered.connect(
            lambda: self.editar_solicitado.emit(self._id_actual)
        )

        menu.addAction(act_editar)
        menu.addSeparator()

        if self._activo_actual:
            act_estado = QAction("⊘   Desactivar cliente", self)
        else:
            act_estado = QAction("✓   Reactivar cliente", self)
        act_estado.triggered.connect(
            lambda: self.desactivar_solicitado.emit(self._id_actual)
        )
        menu.addAction(act_estado)

        menu.addSeparator()

        act_eliminar = QAction("🗑   Eliminar cliente", self)
        act_eliminar.triggered.connect(
            lambda: self.eliminar_solicitado.emit(self._id_actual)
        )
        menu.addAction(act_eliminar)

        # Posicionar debajo del botón ⋯
        pos = self._btn_menu.mapToGlobal(
            QPoint(0, self._btn_menu.height() + 2)
        )
        menu.exec(pos)

    # ──────────────────────────────────────────────────────────────────────────
    # CARGA DE DATOS
    # ──────────────────────────────────────────────────────────────────────────

    def _on_ver_historial(self):
        if self._id_actual:
            dlg = DialogoHistorialCliente(self._conn, self._id_actual, parent=self)
            dlg.exec()

    def cargar(self, conn, id_cliente: int):
        """Carga y muestra los datos del cliente especificado."""
        self._id_actual = id_cliente
        self._conn = conn
        det = qc.obtener_detalle_cliente(conn, id_cliente)
        if det is None:
            return

        self._activo_actual = det["activo"]

        # Cabecera
        self._avatar.setText(_iniciales(det["nombre"]))
        self._lbl_nombre.setText(det["nombre"])
        self._lbl_codigo.setText(
            f"ID #{det['id_cliente']}  ·  {det['condicion_iva']}"
        )

        if det["activo"]:
            self._badge_estado.setText("ACTIVO")
            self._badge_estado.setStyleSheet(
                "background-color: #d1fae5; color: #065f46; border-radius: 10px; "
                "font-size: 10px; font-weight: 700; padding: 0 10px; border: none;"
            )
        else:
            self._badge_estado.setText("INACTIVO")
            self._badge_estado.setStyleSheet(
                "background-color: #fee2e2; color: #991b1b; border-radius: 10px; "
                "font-size: 10px; font-weight: 700; padding: 0 10px; border: none;"
            )

        # Mini métricas
        self._set_mini(self._mk_compras, str(det["total_compras"]))
        self._set_mini(self._mk_total,   _fmt_moneda(det["total_gastado"]))
        self._set_mini(self._mk_ticket,  _fmt_moneda(det["ticket_promedio"]))

        # Info General
        self._f_cuit.set_valor(det["cuit_dni"] or "No registrado")
        self._f_email.set_valor(det["email"] or "No registrado")
        self._f_tel.set_valor(det["telefono"] or "No registrado")
        self._f_dir.set_valor(det["direccion"] or "No registrada")
        self._f_ciu.set_valor(det["ciudad"] or "No registrada")

        # Info Comercial
        self._f_iva.set_valor(det["condicion_iva"])
        ult = det["ultima_compra"]
        self._f_ult_comp.set_valor(ult[:10] if ult else "Sin compras")
        pres = det["presupuestos_activos"]
        self._f_pres_act.set_valor(
            f"{pres} activo(s)" if pres else "Sin presupuestos activos"
        )

        # Actividad reciente
        actividad = qc.obtener_actividad_reciente_cliente(conn, id_cliente, limite=4)
        self._poblar_actividad(actividad)

        # Notas
        self._poblar_notas(conn, id_cliente)

        # Habilitar botones
        self._btn_editar.setEnabled(True)
        self._btn_historial.setEnabled(True)
        self._btn_menu.setEnabled(True)

    def _poblar_actividad(self, actividad: list):
        while self._ly_actividad.count():
            item = self._ly_actividad.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not actividad:
            vacio = QLabel("Sin actividad registrada.")
            vacio.setStyleSheet(
                f"color: {COLOR_TEXT_SEC}; font-size: 12px; border: none;"
            )
            self._ly_actividad.addWidget(vacio)
            return

        for doc in actividad:
            fila = QFrame()
            fila.setStyleSheet(
                f"background-color: {COLOR_BG}; border-radius: 6px; "
                f"border: 1px solid {COLOR_BORDER};"
            )
            ly_f = QHBoxLayout(fila)
            ly_f.setContentsMargins(8, 6, 8, 6)
            ly_f.setSpacing(6)

            tipo = doc["tipo"]
            color_tipo = COLOR_PRIMARY if tipo == "VENTA" else COLOR_WARNING

            lbl_tipo = QLabel("V" if tipo == "VENTA" else "P")
            lbl_tipo.setFixedSize(24, 24)
            lbl_tipo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_tipo.setStyleSheet(
                f"background-color: {color_tipo}; color: white; border-radius: 12px; "
                f"font-size: 10px; font-weight: 800; border: none;"
            )

            info_ly = QVBoxLayout()
            info_ly.setSpacing(1)
            lbl_num = QLabel(doc["numero_interno"])
            lbl_num.setStyleSheet(
                f"color: {COLOR_TEXT_MAIN}; font-size: 11px; font-weight: 700; border: none;"
            )
            fecha = doc["fecha_emision"][:10] if doc["fecha_emision"] else ""
            lbl_fecha = QLabel(f"{fecha}  ·  {doc['estado']}")
            lbl_fecha.setStyleSheet(
                f"color: {COLOR_TEXT_SEC}; font-size: 10px; border: none;"
            )
            info_ly.addWidget(lbl_num)
            info_ly.addWidget(lbl_fecha)

            lbl_total = QLabel(_fmt_moneda(doc["total_final"]))
            lbl_total.setStyleSheet(
                f"color: {COLOR_TEXT_MAIN}; font-size: 12px; font-weight: 800; border: none;"
            )
            lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            ly_f.addWidget(lbl_tipo)
            ly_f.addLayout(info_ly, stretch=1)
            ly_f.addWidget(lbl_total)

            self._ly_actividad.addWidget(fila)



    def _poblar_notas(self, conn, id_cliente: int):
        while self._ly_notas.count():
            item = self._ly_notas.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        notas = qc.obtener_notas_cliente(conn, id_cliente)
        if not notas:
            vacio = QLabel("No hay notas registradas.")
            vacio.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 12px; border: none;")
            self._ly_notas.addWidget(vacio)
            return

        for n in notas:
            fila = QFrame()
            fila.setStyleSheet(f"background-color: #fef9c3; border-radius: 6px; border: 1px solid #fde047;")
            ly_f = QVBoxLayout(fila)
            ly_f.setContentsMargins(8, 6, 8, 6)
            ly_f.setSpacing(4)

            ly_top = QHBoxLayout()
            ly_top.setSpacing(6)
            lbl_fecha = QLabel(n["fecha_hora"])
            lbl_fecha.setStyleSheet(f"color: #a16207; font-size: 10px; font-weight: bold; border: none;")
            ly_top.addWidget(lbl_fecha, stretch=1)

            btn_menu = QPushButton("⋯")
            btn_menu.setFixedSize(20, 20)
            btn_menu.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_menu.setStyleSheet(f"color: #a16207; border: none; font-weight: 900;")
            btn_menu.clicked.connect(lambda checked, id_n=n['id_nota'], btn=btn_menu: self._menu_nota(id_n, btn))
            ly_top.addWidget(btn_menu)
            ly_f.addLayout(ly_top)

            lbl_cont = QLabel(n["contenido"])
            lbl_cont.setWordWrap(True)
            lbl_cont.setStyleSheet(f"color: #854d0e; font-size: 12px; border: none;")
            ly_f.addWidget(lbl_cont)

            self._ly_notas.addWidget(fila)

    def _menu_nota(self, id_nota: int, btn: QPushButton):
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; "
            f"border-radius: 6px; padding: 4px; }}"
            f"QMenu::item {{ padding: 6px 16px; border-radius: 4px; color: {COLOR_TEXT_MAIN}; font-size: 12px; }}"
            f"QMenu::item:selected {{ background-color: {COLOR_BG}; }}"
        )
        act_edit = QAction("Editar", self)
        act_edit.triggered.connect(lambda: self._on_editar_nota(id_nota))
        act_del = QAction("Eliminar", self)
        act_del.triggered.connect(lambda: self._on_eliminar_nota(id_nota))
        menu.addAction(act_edit)
        menu.addAction(act_del)
        menu.exec(btn.mapToGlobal(QPoint(0, btn.height())))

    def _on_add_nota(self):
        dlg = DialogoNota(self._conn, self._id_actual, parent=self)
        if dlg.exec() == dlg.DialogCode.Accepted and dlg.hubo_cambios:
            self.recargar_solicitado.emit(self._id_actual)

    def _on_editar_nota(self, id_nota: int):
        dlg = DialogoNota(self._conn, self._id_actual, id_nota, parent=self)
        if dlg.exec() == dlg.DialogCode.Accepted and dlg.hubo_cambios:
            self.recargar_solicitado.emit(self._id_actual)

    def _on_eliminar_nota(self, id_nota: int):
        resp = QMessageBox.question(
            self, "Eliminar Nota", "¿Está seguro de eliminar esta nota?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            qc.eliminar_nota(self._conn, id_nota)
            self.recargar_solicitado.emit(self._id_actual)



# ══════════════════════════════════════════════════════════════════════════════
# PESTAÑA PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class PestanaClientes(QWidget):
    """
    Vista principal de la pestaña Clientes con CRUD completo.

    Puerto público:
        recargar() — fuerza recarga completa manteniendo filtro y página actual
    """

    _OPCIONES_POR_PAGINA = [20, 50, 100]

    def __init__(self, conexion_db):
        super().__init__()
        self.conn = conexion_db
        self._filtro: str = ""
        self._filtros_avanzados = {
            "estado": "TODOS",
            "con_compras": "TODOS",
            "condicion_iva": "TODAS"
        }
        self._pagina_actual: int = 1
        self._por_pagina      = 20
        self._total_paginas   = 1
        self._actualizando_tabla = False
        self._filtro          = ""
        self._id_cliente_seleccionado: int | None = None

        # Debounce para búsqueda (evita consultas en cada tecla)
        self._timer_busqueda = QTimer(self)
        self._timer_busqueda.setSingleShot(True)
        self._timer_busqueda.setInterval(350)
        self._timer_busqueda.timeout.connect(self._aplicar_busqueda)

        self._init_ui()
        
        # Conectar panel lateral para recargas parciales (contactos/notas)
        self._panel_detalle.recargar_solicitado.connect(self._on_recarga_parcial)
        
        self.recargar()

    # ──────────────────────────────────────────────────────────────────────────
    # CONSTRUCCIÓN DE LA UI
    # ──────────────────────────────────────────────────────────────────────────

    def _init_ui(self):
        self.setStyleSheet(self._stylesheet())
        ly = QVBoxLayout(self)
        ly.setContentsMargins(20, 16, 20, 16)
        ly.setSpacing(14)

        ly.addLayout(self._construir_encabezado())
        ly.addLayout(self._construir_metricas())
        ly.addLayout(self._construir_herramientas())

        self._panel_filtros = self._construir_panel_filtros()
        ly.addWidget(self._panel_filtros)

        ly.addWidget(self._construir_cuerpo(), stretch=1)
        ly.addLayout(self._construir_paginacion())

    def _stylesheet(self) -> str:
        return f"""
            PestanaClientes {{ background-color: {COLOR_BG}; }}
            QLineEdit {{
                padding: 8px 12px; font-size: 13px;
                border: 1px solid {COLOR_BORDER}; border-radius: 6px;
                background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_MAIN};
            }}
            QLineEdit:focus {{ border: 2px solid {COLOR_PRIMARY}; }}
            QPushButton.primario {{
                background-color: {COLOR_PRIMARY}; color: white;
                font-weight: bold; font-size: 13px;
                padding: 8px 16px; border-radius: 6px; border: none;
            }}
            QPushButton.primario:hover {{ background-color: #1d4ed8; }}
            QPushButton.secundario {{
                background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_MAIN};
                font-weight: 600; font-size: 13px;
                padding: 8px 14px; border-radius: 6px;
                border: 1px solid {COLOR_BORDER};
            }}
            QPushButton.secundario:hover {{ background-color: {COLOR_BG}; }}
            QPushButton.pagina {{
                background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_MAIN};
                font-size: 13px; padding: 5px 12px;
                border-radius: 5px; border: 1px solid {COLOR_BORDER}; min-width: 32px;
            }}
            QPushButton.pagina:hover {{ background-color: {COLOR_BG}; border-color: {COLOR_PRIMARY}; }}
            QPushButton.pagina:disabled {{ color: {COLOR_BORDER}; background-color: {COLOR_BG}; }}
            QTableWidget {{
                border: 1px solid {COLOR_BORDER}; border-radius: 8px;
                gridline-color: {COLOR_BORDER};
                background-color: {COLOR_CARD_BG}; outline: none; font-size: 13px;
            }}
            QHeaderView::section {{
                background-color: {COLOR_BG}; color: {COLOR_TEXT_SEC};
                font-weight: 700; font-size: 12px;
                border: none; border-bottom: 1px solid {COLOR_BORDER}; padding: 10px 8px;
            }}
            QTableWidget::item {{
                border-bottom: 1px solid #f1f5f9;
                padding: 4px 8px; color: {COLOR_TEXT_MAIN};
            }}
            QTableWidget::item:selected {{
                background-color: #ebf5ff; color: {COLOR_TEXT_MAIN};
            }}
            QComboBox {{
                padding: 5px 8px; font-size: 12px;
                border: 1px solid {COLOR_BORDER}; border-radius: 5px;
                background-color: {COLOR_CARD_BG}; color: {COLOR_TEXT_MAIN}; min-width: 70px;
            }}
        """

    def _construir_encabezado(self) -> QHBoxLayout:
        ly = QHBoxLayout()
        ly.setSpacing(12)

        ly_tit = QVBoxLayout()
        ly_tit.setSpacing(2)
        lbl_tit = QLabel("Clientes")
        lbl_tit.setStyleSheet(
            f"font-size: 22px; font-weight: 900; color: {COLOR_TEXT_MAIN};"
        )
        lbl_sub = QLabel("Gestión de clientes")
        lbl_sub.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_SEC};")
        ly_tit.addWidget(lbl_tit)
        ly_tit.addWidget(lbl_sub)

        ly.addLayout(ly_tit)
        ly.addStretch()

        return ly

    def _construir_herramientas(self) -> QHBoxLayout:
        ly = QHBoxLayout()
        ly.setSpacing(12)

        self._input_busqueda = QLineEdit()
        self._input_busqueda.setPlaceholderText(
            "Buscar cliente por nombre, CUIT o email... (F2)"
        )
        self._input_busqueda.setMinimumWidth(300)
        self._input_busqueda.setFixedHeight(36)
        self._input_busqueda.textChanged.connect(self._on_texto_cambiado)

        self._btn_filtros = QPushButton("⚙  Filtros")
        self._btn_filtros.setProperty("class", "secundario")
        self._btn_filtros.setFixedHeight(36)
        self._btn_filtros.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_filtros.clicked.connect(self._toggle_filtros)

        self._btn_nuevo = QPushButton("＋  Nuevo Cliente")
        self._btn_nuevo.setProperty("class", "primario")
        self._btn_nuevo.setFixedHeight(36)
        self._btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_nuevo.setShortcut(QKeySequence("Ctrl+N"))
        self._btn_nuevo.clicked.connect(self._on_nuevo_cliente)
        self._btn_nuevo.setToolTip("Nuevo cliente (Ctrl+N)")

        ly.addWidget(self._input_busqueda)
        ly.addWidget(self._btn_filtros)
        ly.addStretch()
        ly.addWidget(self._btn_nuevo)
        
        return ly

    def _construir_panel_filtros(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel_filtros")
        panel.setStyleSheet(
            f"#panel_filtros {{ background-color: {COLOR_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 6px; }}"
        )
        panel.setVisible(False)
        
        ly = QHBoxLayout(panel)
        ly.setContentsMargins(12, 10, 12, 10)
        ly.setSpacing(16)
        


        # Estado
        ly_estado = QVBoxLayout()
        ly_estado.setSpacing(4)
        lbl_est = QLabel("Estado")
        lbl_est.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 11px; font-weight: bold;")
        self._cb_f_estado = QComboBox()
        self._cb_f_estado.addItems(["TODOS", "ACTIVOS", "INACTIVOS"])
        self._cb_f_estado.currentIndexChanged.connect(self._aplicar_filtros_desde_ui)
        ly_estado.addWidget(lbl_est)
        ly_estado.addWidget(self._cb_f_estado)
        ly.addLayout(ly_estado)

        # Historial comercial
        ly_compras = QVBoxLayout()
        ly_compras.setSpacing(4)
        lbl_comp = QLabel("Historial comercial")
        lbl_comp.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 11px; font-weight: bold;")
        self._cb_f_compras = QComboBox()
        self._cb_f_compras.addItems(["TODOS", "SI", "NO"])
        self._cb_f_compras.currentIndexChanged.connect(self._aplicar_filtros_desde_ui)
        ly_compras.addWidget(lbl_comp)
        ly_compras.addWidget(self._cb_f_compras)
        ly.addLayout(ly_compras)

        # Condición IVA
        ly_iva = QVBoxLayout()
        ly_iva.setSpacing(4)
        lbl_iva = QLabel("Condición IVA")
        lbl_iva.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 11px; font-weight: bold;")
        self._cb_f_iva = QComboBox()
        self._cb_f_iva.addItems(["TODAS", "Consumidor Final", "Responsable Inscripto", "Monotributista", "Exento", "No Responsable"])
        self._cb_f_iva.currentIndexChanged.connect(self._aplicar_filtros_desde_ui)
        ly_iva.addWidget(lbl_iva)
        ly_iva.addWidget(self._cb_f_iva)
        ly.addLayout(ly_iva)
        
        # Localidad
        ly_loc = QVBoxLayout()
        ly_loc.setSpacing(4)
        lbl_loc = QLabel("Localidad")
        lbl_loc.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 11px; font-weight: bold;")
        self._cb_f_loc = QComboBox()
        self._cb_f_loc.addItem("TODAS")
        self._cb_f_loc.currentIndexChanged.connect(self._aplicar_filtros_desde_ui)
        # Se poblará luego
        ly_loc.addWidget(lbl_loc)
        ly_loc.addWidget(self._cb_f_loc)
        ly.addLayout(ly_loc)

        ly.addStretch()
        
        # Botones
        ly_btns = QVBoxLayout()
        ly_btns.setAlignment(Qt.AlignmentFlag.AlignBottom)
        ly_btns_h = QHBoxLayout()
        ly_btns_h.setSpacing(8)
        
        self._btn_limpiar_filtros = QPushButton("Limpiar")
        self._btn_limpiar_filtros.setProperty("class", "secundario")
        self._btn_limpiar_filtros.clicked.connect(self._limpiar_filtros)
        
        ly_btns_h.addWidget(self._btn_limpiar_filtros)
        ly_btns.addLayout(ly_btns_h)
        ly.addLayout(ly_btns)

        return panel

    def _toggle_filtros(self):
        visible = not self._panel_filtros.isVisible()
        self._panel_filtros.setVisible(visible)
        
        if visible:
            # Actualizar localidades si se despliega
            actuales = [self._cb_f_loc.itemText(i) for i in range(self._cb_f_loc.count())]
            ciudades = qc.obtener_ciudades(self.conn)
            ciudades = ["TODAS"] + ciudades
            if set(actuales) != set(ciudades):
                self._cb_f_loc.blockSignals(True)
                self._cb_f_loc.clear()
                self._cb_f_loc.addItems(ciudades)
                self._cb_f_loc.blockSignals(False)

    def _limpiar_filtros(self):
        for cb in (self._cb_f_estado, self._cb_f_compras, self._cb_f_iva, self._cb_f_loc):
            cb.blockSignals(True)
            cb.setCurrentIndex(0)
            cb.blockSignals(False)
        self._aplicar_filtros_desde_ui()

    def _aplicar_filtros_desde_ui(self):
        estado = self._cb_f_estado.currentText()
        compras = self._cb_f_compras.currentText()
        iva = self._cb_f_iva.currentText()
        loc = self._cb_f_loc.currentText()
        
        self._filtros_avanzados["estado"] = estado
        self._filtros_avanzados["con_compras"] = compras
        self._filtros_avanzados["condicion_iva"] = iva
        self._filtros_avanzados["ciudad"] = loc
        
        activos = 0
        if estado != "TODOS": activos += 1
        if compras != "TODOS": activos += 1
        if iva != "TODAS": activos += 1
        if loc != "TODAS": activos += 1
        
        if activos > 0:
            self._btn_filtros.setText(f"⚙  Filtros ({activos})")
            self._btn_filtros.setStyleSheet(f"color: {COLOR_PRIMARY}; border-color: {COLOR_PRIMARY}; font-weight: bold;")
        else:
            self._btn_filtros.setText("⚙  Filtros")
            self._btn_filtros.setStyleSheet("") # reset
            
        self._pagina_actual = 1
        self._cargar_tabla()

    def _construir_metricas(self) -> QHBoxLayout:
        ly = QHBoxLayout()
        ly.setSpacing(10)

        self._t_total   = _TarjetaMetrica("Total Clientes", "—", COLOR_PRIMARY)
        self._t_activos = _TarjetaMetrica("Activos",        "—", COLOR_SUCCESS)
        self._t_compras = _TarjetaMetrica("Con Compras",    "—", COLOR_WARNING)
        self._t_ventas  = _TarjetaMetrica("Ventas (Mes)",   "—", "#8b5cf6")
        self._t_ticket  = _TarjetaMetrica("Ticket Promedio","—", "#0ea5e9")

        for t in (self._t_total, self._t_activos, self._t_compras,
                  self._t_ventas, self._t_ticket):
            ly.addWidget(t, stretch=1)
        return ly

    def _construir_cuerpo(self) -> QSplitter:
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(6)
        self._splitter.setChildrenCollapsible(False)

        # ── Tabla ──────────────────────────────────────────────────────────
        contenedor_tabla = QFrame()
        contenedor_tabla.setStyleSheet(
            f"background-color: {COLOR_CARD_BG}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 8px;"
        )
        ly_ct = QVBoxLayout(contenedor_tabla)
        ly_ct.setContentsMargins(0, 0, 0, 0)

        self._tabla = QTableWidget()
        self._tabla.setColumnCount(8)
        self._tabla.setHorizontalHeaderLabels([
            "Código", "Nombre / Razón Social", "CUIT", "Condición IVA",
            "Email", "Teléfono", "Ciudad", "Saldo Actual"
        ])
        self._tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tabla.verticalHeader().setVisible(False)
        self._tabla.setShowGrid(True)
        self._tabla.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._tabla.verticalHeader().setDefaultSectionSize(38)

        hdr = self._tabla.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        self._tabla.itemSelectionChanged.connect(self._on_seleccion_cambiada)

        ly_ct.addWidget(self._tabla)

        # ── Panel lateral ──────────────────────────────────────────────────
        self._stack_panel = QStackedWidget()
        self._stack_panel.setMinimumWidth(270)
        self._stack_panel.setMaximumWidth(380)
        self._stack_panel.setStyleSheet(
            f"border: 1px solid {COLOR_BORDER}; border-radius: 8px; "
            f"background-color: {COLOR_CARD_BG};"
        )

        self._panel_vacio   = _PanelVacio()
        self._panel_detalle = _PanelDetalle()
        self._panel_detalle.editar_solicitado.connect(self._on_editar_cliente)
        self._panel_detalle.desactivar_solicitado.connect(self._on_desactivar_cliente)
        self._panel_detalle.eliminar_solicitado.connect(self._on_eliminar_cliente)

        self._stack_panel.addWidget(self._panel_vacio)    # índice 0
        self._stack_panel.addWidget(self._panel_detalle)  # índice 1
        self._stack_panel.setCurrentIndex(0)

        self._splitter.addWidget(contenedor_tabla)
        self._splitter.addWidget(self._stack_panel)
        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setSizes([700, 300])

        return self._splitter

    def _construir_paginacion(self) -> QHBoxLayout:
        ly = QHBoxLayout()
        ly.setSpacing(8)

        self._lbl_info_pagina = QLabel("Sin resultados")
        self._lbl_info_pagina.setStyleSheet(
            f"color: {COLOR_TEXT_SEC}; font-size: 12px;"
        )

        ly.addWidget(self._lbl_info_pagina)
        ly.addStretch()

        lbl_pp = QLabel("Filas:")
        lbl_pp.setStyleSheet(f"color: {COLOR_TEXT_SEC}; font-size: 12px;")
        self._combo_por_pagina = QComboBox()
        for op in self._OPCIONES_POR_PAGINA:
            self._combo_por_pagina.addItem(str(op), op)
        self._combo_por_pagina.currentIndexChanged.connect(
            self._on_por_pagina_cambiado
        )

        self._btn_prev = QPushButton("← Anterior")
        self._btn_prev.setProperty("class", "pagina")
        self._btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_prev.clicked.connect(self._pagina_anterior)

        self._lbl_pagina = QLabel("Página 1 / 1")
        self._lbl_pagina.setStyleSheet(
            f"color: {COLOR_TEXT_SEC}; font-size: 12px; padding: 0 4px;"
        )
        self._lbl_pagina.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._btn_next = QPushButton("Siguiente →")
        self._btn_next.setProperty("class", "pagina")
        self._btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_next.clicked.connect(self._pagina_siguiente)

        ly.addWidget(lbl_pp)
        ly.addWidget(self._combo_por_pagina)
        ly.addSpacing(8)
        ly.addWidget(self._btn_prev)
        ly.addWidget(self._lbl_pagina)
        ly.addWidget(self._btn_next)
        return ly

    # ──────────────────────────────────────────────────────────────────────────
    # CARGA DE DATOS
    # ──────────────────────────────────────────────────────────────────────────

    def recargar(self):
        """Recarga métricas y tabla conservando filtro, página y selección actuales."""
        self._cargar_metricas()
        self._cargar_tabla()

    def _cargar_metricas(self):
        try:
            m = qc.obtener_metricas_clientes(self.conn)
            self._t_total.set_valor(str(m["total"]))
            self._t_activos.set_valor(str(m["activos"]))
            self._t_compras.set_valor(str(m["con_compras"]))
            self._t_ventas.set_valor(_fmt_moneda(m["ventas_mes"]))
            self._t_ticket.set_valor(_fmt_moneda(m["ticket_promedio"]))
        except Exception as e:
            print(f"[Clientes] Error cargando métricas: {e}")

    def _cargar_tabla(self):
        try:
            resultado = qc.obtener_clientes(
                self.conn,
                filtro=self._filtro,
                estado=self._filtros_avanzados["estado"],
                con_compras=self._filtros_avanzados["con_compras"],
                condicion_iva=self._filtros_avanzados["condicion_iva"],
                ciudad=self._filtros_avanzados.get("ciudad", "TODAS"),
                pagina=self._pagina_actual,
                por_pagina=self._por_pagina,
            )
        except Exception as e:
            print(f"[Clientes] Error cargando tabla: {e}")
            return

        filas       = resultado["filas"]
        total_filas = resultado["total_filas"]
        self._total_paginas = resultado["total_paginas"]

        self._actualizando_tabla = True
        self._tabla.setRowCount(0)
        
        for datos in filas:
            row = self._tabla.rowCount()
            self._tabla.insertRow(row)
            self._tabla.setRowHeight(row, 38)

            items = [
                (str(datos["id_cliente"]),    Qt.AlignmentFlag.AlignCenter),
                (datos["nombre"],             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (datos["cuit_dni"] or "—",    Qt.AlignmentFlag.AlignCenter),
                (datos.get("condicion_iva", "—"), Qt.AlignmentFlag.AlignCenter),
                (datos["email"] or "—",       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (datos["telefono"] or "—",    Qt.AlignmentFlag.AlignCenter),
                (datos["ciudad"] or "—",      Qt.AlignmentFlag.AlignCenter),
                ("N/D",                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
            ]
            for col, (texto, alineacion) in enumerate(items):
                item = QTableWidgetItem(texto)
                item.setTextAlignment(alineacion)
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, datos["id_cliente"])
                if not datos["activo"]:
                    item.setForeground(QColor(COLOR_TEXT_SEC))
                if col == 6:
                    item.setForeground(QColor(COLOR_TEXT_SEC))
                self._tabla.setItem(row, col, item)

        self._actualizando_tabla = False
        self._actualizar_controles_paginacion(total_filas)

        # Re-seleccionar el cliente activo si aún está en la página
        if self._id_cliente_seleccionado is not None:
            encontrado = self._seleccionar_por_id(self._id_cliente_seleccionado)
            if not encontrado:
                self._stack_panel.setCurrentIndex(0)

    def _actualizar_controles_paginacion(self, total_filas: int):
        inicio = (self._pagina_actual - 1) * self._por_pagina + 1 if total_filas > 0 else 0
        fin    = min(self._pagina_actual * self._por_pagina, total_filas)
        self._lbl_info_pagina.setText(
            f"Mostrando {inicio}–{fin} de {total_filas} cliente(s)"
            if total_filas > 0 else "Sin clientes registrados"
        )
        self._lbl_pagina.setText(f"Página {self._pagina_actual} / {self._total_paginas}")
        self._btn_prev.setEnabled(self._pagina_actual > 1)
        self._btn_next.setEnabled(self._pagina_actual < self._total_paginas)

    # ──────────────────────────────────────────────────────────────────────────
    # HELPERS DE SELECCIÓN
    # ──────────────────────────────────────────────────────────────────────────

    def _seleccionar_por_id(self, id_cliente: int) -> bool:
        """
        Selecciona la fila correspondiente al id_cliente en la tabla.
        Retorna True si se encontró y seleccionó.
        """
        for row in range(self._tabla.rowCount()):
            item = self._tabla.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == id_cliente:
                self._tabla.blockSignals(True)
                self._tabla.selectRow(row)
                self._tabla.blockSignals(False)
                self._tabla.scrollToItem(item)
                return True
        return False

    # ──────────────────────────────────────────────────────────────────────────
    # HANDLERS DE EVENTOS DE UI
    # ──────────────────────────────────────────────────────────────────────────

    def _on_texto_cambiado(self, texto: str):
        self._filtro = texto.strip()
        self._timer_busqueda.stop()
        self._timer_busqueda.start()



    def _on_recarga_parcial(self, id_cliente: int):
        if id_cliente > 0:
            self._panel_detalle.cargar(self.conn, id_cliente)
        elif id_cliente < 0:
            # Hack for delete signals not passing conn
            pass # handled elsewhere now

    def _aplicar_busqueda(self):
        self._pagina_actual = 1
        self._id_cliente_seleccionado = None
        self._stack_panel.setCurrentIndex(0)
        self._cargar_tabla()

    def _on_seleccion_cambiada(self):
        if self._actualizando_tabla:
            return
            
        filas = self._tabla.selectedItems()
        if not filas:
            self._stack_panel.setCurrentIndex(0)
            self._id_cliente_seleccionado = None
            return

        fila = self._tabla.currentRow()
        item_cod = self._tabla.item(fila, 0)
        if item_cod is None:
            return
        id_cliente = item_cod.data(Qt.ItemDataRole.UserRole)
        if id_cliente == self._id_cliente_seleccionado:
            return

        self._id_cliente_seleccionado = id_cliente
        self._stack_panel.setCurrentIndex(1)
        try:
            self._panel_detalle.cargar(self.conn, id_cliente)
        except Exception as e:
            print(f"[Clientes] Error cargando detalle: {e}")
            self._stack_panel.setCurrentIndex(0)

    def _on_por_pagina_cambiado(self, index: int):
        self._por_pagina = self._combo_por_pagina.itemData(index)
        self._pagina_actual = 1
        self._cargar_tabla()

    def _pagina_anterior(self):
        if self._pagina_actual > 1:
            self._pagina_actual -= 1
            self._cargar_tabla()

    def _pagina_siguiente(self):
        if self._pagina_actual < self._total_paginas:
            self._pagina_actual += 1
            self._cargar_tabla()

    # ──────────────────────────────────────────────────────────────────────────
    # CRUD — NUEVO CLIENTE
    # ──────────────────────────────────────────────────────────────────────────

    def _on_nuevo_cliente(self):
        from ui.dialogs_clientes import DialogoFormularioCliente
        formulario = DialogoFormularioCliente(self.conn, parent=self)
        if formulario.exec() == QDialog.DialogCode.Accepted and formulario.id_guardado is not None:
            nuevo_id = formulario.id_guardado
            # Ir a la primera página para que sea visible
            self._pagina_actual = 1
            self._id_cliente_seleccionado = nuevo_id
            self.recargar()
            # Intentar seleccionar; si no está en esta página, solo refrescar
            if not self._seleccionar_por_id(nuevo_id):
                self._stack_panel.setCurrentIndex(0)
            else:
                self._panel_detalle.cargar(self.conn, nuevo_id)
                self._stack_panel.setCurrentIndex(1)

    # ──────────────────────────────────────────────────────────────────────────
    # CRUD — EDITAR CLIENTE
    # ──────────────────────────────────────────────────────────────────────────

    def _on_editar_cliente(self, id_cliente: int):
        from ui.dialogs_clientes import DialogoFormularioCliente
        formulario = DialogoFormularioCliente(self.conn, id_cliente=id_cliente, parent=self)
        if formulario.exec() == QDialog.DialogCode.Accepted and formulario.id_guardado is not None:
            self._id_cliente_seleccionado = id_cliente
            self.recargar()
            # Actualizar panel lateral con nuevos datos
            self._panel_detalle.cargar(self.conn, id_cliente)
            self._stack_panel.setCurrentIndex(1)

    # ──────────────────────────────────────────────────────────────────────────
    # CRUD — DESACTIVAR / REACTIVAR
    # ──────────────────────────────────────────────────────────────────────────

    def _on_desactivar_cliente(self, id_cliente: int):
        det = qc.obtener_detalle_cliente(self.conn, id_cliente)
        if det is None:
            return

        if det["activo"]:
            resp = QMessageBox.question(
                self,
                "Desactivar cliente",
                f"¿Desactivar al cliente <b>{det['nombre']}</b>?<br><br>"
                f"El cliente ya no aparecerá en las búsquedas activas, "
                f"pero su historial se conservará.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp == QMessageBox.StandardButton.Yes:
                qc.desactivar_cliente(self.conn, id_cliente)
                self._id_cliente_seleccionado = id_cliente
                self.recargar()
                self._panel_detalle.cargar(self.conn, id_cliente)
                self._stack_panel.setCurrentIndex(1)
        else:
            resp = QMessageBox.question(
                self,
                "Reactivar cliente",
                f"¿Reactivar al cliente <b>{det['nombre']}</b>?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if resp == QMessageBox.StandardButton.Yes:
                qc.reactivar_cliente(self.conn, id_cliente)
                self._id_cliente_seleccionado = id_cliente
                self.recargar()
                self._panel_detalle.cargar(self.conn, id_cliente)
                self._stack_panel.setCurrentIndex(1)

    # ──────────────────────────────────────────────────────────────────────────
    # CRUD — ELIMINAR CLIENTE
    # ──────────────────────────────────────────────────────────────────────────

    def _on_eliminar_cliente(self, id_cliente: int):
        det = qc.obtener_detalle_cliente(self.conn, id_cliente)
        if det is None:
            return

        tiene_docs = qc.tiene_documentos(self.conn, id_cliente)

        if tiene_docs:
            # Cliente con historial → ofrecer desactivación en su lugar
            resp = QMessageBox.warning(
                self,
                "Cliente con historial comercial",
                f"El cliente <b>{det['nombre']}</b> tiene documentos (ventas o "
                f"presupuestos) asociados.<br><br>"
                f"Eliminarlo podría comprometer el historial comercial del sistema.<br><br>"
                f"<b>¿Desactivarlo en su lugar?</b> (el historial se conservará)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if resp == QMessageBox.StandardButton.Yes:
                qc.desactivar_cliente(self.conn, id_cliente)
                self._id_cliente_seleccionado = id_cliente
                self.recargar()
                self._panel_detalle.cargar(self.conn, id_cliente)
                self._stack_panel.setCurrentIndex(1)
        else:
            # Sin documentos → eliminar físicamente con confirmación
            resp = QMessageBox.warning(
                self,
                "Eliminar cliente",
                f"¿Eliminar definitivamente al cliente <b>{det['nombre']}</b>?<br><br>"
                f"Este cliente no tiene documentos asociados.<br>"
                f"<b>Esta acción no se puede deshacer.</b>",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp == QMessageBox.StandardButton.Yes:
                try:
                    qc.eliminar_cliente(self.conn, id_cliente)
                    self._id_cliente_seleccionado = None
                    self._stack_panel.setCurrentIndex(0)
                    self.recargar()
                except Exception as e:
                    QMessageBox.critical(
                        self, "Error", f"No se pudo eliminar el cliente:\n{e}"
                    )

    # ──────────────────────────────────────────────────────────────────────────
    # ATAJOS DE TECLADO
    # ──────────────────────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F2:
            self._input_busqueda.setFocus()
            self._input_busqueda.selectAll()
        else:
            super().keyPressEvent(event)
