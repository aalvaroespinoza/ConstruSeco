"""
ui/dialogs_contactos_notas.py — Formularios modales para Notas y Contactos.

Responsabilidades:
  - DialogoNota: crear/editar notas de un cliente.
  - DialogoContacto: crear/editar contactos de un cliente.
"""

from ui.core.modal import DialogoModalIntegrado
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QCheckBox, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt

from ui.core.theme import (
    COLOR_PRIMARY, COLOR_BG, COLOR_CARD_BG, COLOR_TEXT_MAIN,
    COLOR_TEXT_SEC, COLOR_BORDER, COLOR_DANGER
)
from db import queries_clientes as qc
from ui.modules.clientes.dialogs_clientes import _CampoFormulario, _RE_EMAIL, _RE_TEL


class DialogoNota(DialogoModalIntegrado):
    def __init__(self, conn, id_cliente: int, id_nota: int | None = None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.id_cliente = id_cliente
        self.id_nota = id_nota
        self.modo_edicion = id_nota is not None
        self.hubo_cambios = False

        self.setWindowTitle("Editar Nota" if self.modo_edicion else "Nueva Nota")
        self.setMinimumWidth(480)
        self.setMinimumHeight(300)
        

        self._construir_ui()
        if self.modo_edicion:
            self._precargar()

    def _construir_ui(self):
        ly = QVBoxLayout(self)
        ly.setContentsMargins(24, 24, 24, 24)
        ly.setSpacing(16)

        lbl_titulo = QLabel("Escribí el contenido de la nota:")
        lbl_titulo.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {COLOR_TEXT_MAIN};")
        ly.addWidget(lbl_titulo)

        self.txt_contenido = QTextEdit()
        self.txt_contenido.setPlaceholderText("Escribí el contenido de la nota...")
        self.txt_contenido.setStyleSheet(
            f"border: 1px solid {COLOR_BORDER}; border-radius: 6px; padding: 8px; "
            f"background-color: {COLOR_BG}; color: {COLOR_TEXT_MAIN}; font-size: 13px;"
        )
        ly.addWidget(self.txt_contenido)

        self._lbl_error = QLabel("")
        self._lbl_error.setStyleSheet(f"color: {COLOR_DANGER}; font-size: 12px;")
        self._lbl_error.setVisible(False)
        ly.addWidget(self._lbl_error)

        ly_btns = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet(
            f"background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; "
            f"border-radius: 6px; padding: 8px 16px; color: {COLOR_TEXT_MAIN};"
        )
        btn_cancelar.clicked.connect(self.reject)

        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setStyleSheet(
            f"background-color: {COLOR_PRIMARY}; border: none; border-radius: 6px; "
            f"padding: 8px 16px; color: white; font-weight: bold;"
        )
        self.btn_guardar.clicked.connect(self._guardar)

        ly_btns.addStretch()
        ly_btns.addWidget(btn_cancelar)
        ly_btns.addWidget(self.btn_guardar)
        ly.addLayout(ly_btns)

    def _precargar(self):
        notas = qc.obtener_notas_cliente(self.conn, self.id_cliente)
        nota = next((n for n in notas if n["id_nota"] == self.id_nota), None)
        if nota:
            self.txt_contenido.setPlainText(nota["contenido"])

    def _guardar(self):
        cont = self.txt_contenido.toPlainText().strip()
        if not cont:
            self._lbl_error.setText("La nota no puede estar vacía.")
            self._lbl_error.setVisible(True)
            return

        self.btn_guardar.setEnabled(False)
        try:
            if self.modo_edicion:
                qc.actualizar_nota(self.conn, self.id_nota, cont)
            else:
                qc.guardar_nota(self.conn, self.id_cliente, cont)
            self.hubo_cambios = True
            self.accept()
        except Exception as e:
            self._lbl_error.setText(str(e))
            self._lbl_error.setVisible(True)
        finally:
            self.btn_guardar.setEnabled(True)


class DialogoContacto(DialogoModalIntegrado):
    def __init__(self, conn, id_cliente: int, id_contacto: int | None = None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.id_cliente = id_cliente
        self.id_contacto = id_contacto
        self.modo_edicion = id_contacto is not None
        self.hubo_cambios = False

        self.setWindowTitle("Editar Contacto" if self.modo_edicion else "Nuevo Contacto")
        self.setMinimumWidth(520)
        

        self._campos = {}
        self._construir_ui()
        if self.modo_edicion:
            self._precargar()

    def _construir_ui(self):
        ly = QVBoxLayout(self)
        ly.setContentsMargins(24, 24, 24, 24)
        ly.setSpacing(16)

        lbl_titulo = QLabel("Completá los datos del contacto:")
        lbl_titulo.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {COLOR_TEXT_MAIN};")
        ly.addWidget(lbl_titulo)

        inp_nombre = QLineEdit()
        self._campos["nombre"] = _CampoFormulario("Nombre", inp_nombre, requerido=True)
        ly.addWidget(self._campos["nombre"])

        inp_cargo = QLineEdit()
        self._campos["cargo"] = _CampoFormulario("Cargo / Rol", inp_cargo)
        ly.addWidget(self._campos["cargo"])

        fila_te = QHBoxLayout()
        inp_tel = QLineEdit()
        self._campos["telefono"] = _CampoFormulario("Teléfono", inp_tel)
        inp_email = QLineEdit()
        self._campos["email"] = _CampoFormulario("Email", inp_email)
        fila_te.addWidget(self._campos["telefono"])
        fila_te.addWidget(self._campos["email"])
        ly.addLayout(fila_te)

        self.chk_principal = QCheckBox("Marcar como contacto principal")
        self.chk_principal.setToolTip("Al marcar este contacto como principal, el anterior principal pasará a secundario.")
        self.chk_principal.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-size: 13px;")
        ly.addWidget(self.chk_principal)

        self._lbl_error = QLabel("")
        self._lbl_error.setStyleSheet(f"color: {COLOR_DANGER}; font-size: 12px;")
        self._lbl_error.setVisible(False)
        ly.addWidget(self._lbl_error)

        ly_btns = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet(
            f"background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; "
            f"border-radius: 6px; padding: 8px 16px; color: {COLOR_TEXT_MAIN};"
        )
        btn_cancelar.clicked.connect(self.reject)

        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setStyleSheet(
            f"background-color: {COLOR_PRIMARY}; border: none; border-radius: 6px; "
            f"padding: 8px 16px; color: white; font-weight: bold;"
        )
        self.btn_guardar.clicked.connect(self._guardar)

        ly_btns.addStretch()
        ly_btns.addWidget(btn_cancelar)
        ly_btns.addWidget(self.btn_guardar)
        ly.addLayout(ly_btns)

    def _precargar(self):
        contactos = qc.obtener_contactos_cliente(self.conn, self.id_cliente)
        contacto = next((c for c in contactos if c["id_contacto"] == self.id_contacto), None)
        if contacto:
            self._campos["nombre"].widget.setText(contacto["nombre"])
            self._campos["cargo"].widget.setText(contacto["cargo"] or "")
            self._campos["telefono"].widget.setText(contacto["telefono"] or "")
            self._campos["email"].widget.setText(contacto["email"] or "")
            self.chk_principal.setChecked(bool(contacto["principal"]))

    def _txt(self, k):
        return self._campos[k].widget.text().strip()

    def _guardar(self):
        for c in self._campos.values():
            c.clear_error()
        self._lbl_error.setVisible(False)

        hay_error = False
        nombre = self._txt("nombre")
        if not nombre:
            self._campos["nombre"].set_error("El nombre es obligatorio.")
            hay_error = True

        email = self._txt("email")
        if email and not _RE_EMAIL.match(email):
            self._campos["email"].set_error("Email inválido. Ejemplo: nombre@dominio.com")
            hay_error = True

        tel = self._txt("telefono")
        if tel and not _RE_TEL.match(tel):
            self._campos["telefono"].set_error("Teléfono inválido. Solo se aceptan números y + - ( ).")
            hay_error = True

        if hay_error:
            return

        datos = {
            "id_cliente": self.id_cliente,
            "nombre": nombre,
            "cargo": self._txt("cargo"),
            "telefono": tel,
            "email": email,
            "principal": self.chk_principal.isChecked(),
        }

        self.btn_guardar.setEnabled(False)
        try:
            if self.modo_edicion:
                qc.actualizar_contacto(self.conn, self.id_contacto, datos)
            else:
                qc.guardar_contacto(self.conn, self.id_cliente, datos)
            self.hubo_cambios = True
            self.accept()
        except Exception as e:
            self._lbl_error.setText(str(e))
            self._lbl_error.setVisible(True)
        finally:
            self.btn_guardar.setEnabled(True)
