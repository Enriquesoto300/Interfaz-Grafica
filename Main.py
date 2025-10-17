import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

# ============================================================
# CLASE MODELO: Gestión de la Lógica de Negocio y Base de Datos
# ============================================================
class EmpleadoModel:
    """
    Se encarga de toda la comunicación con la base de datos MySQL.
    """
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
        self.cursor = None

    def _conectar(self):
        """Establece la conexión con la base de datos."""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            self.cursor = self.connection.cursor(dictionary=True)
        except mysql.connector.Error as err:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar a la base de datos: {err}")
            return False
        return True

    def _desconectar(self):
        """Cierra la conexión con la base de datos."""
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()

    def obtener_empleados(self):
        """Recupera todos los empleados de la base de datos."""
        if not self._conectar():
            return []
        
        try:
            self.cursor.execute("SELECT id, nombre, sexo, correo FROM empleados ORDER BY id")
            empleados = self.cursor.fetchall()
            return empleados
        except mysql.connector.Error as err:
            messagebox.showerror("Error de Consulta", f"No se pudo obtener la lista de empleados: {err}")
            return []
        finally:
            self._desconectar()

    def agregar_empleado(self, nombre, sexo, correo):
        """
        Agrega un nuevo empleado a la base de datos usando consultas parametrizadas.
        """
        if not self._conectar():
            return False
            
        try:
            # Consulta segura para prevenir inyección SQL
            query = "INSERT INTO empleados (nombre, sexo, correo) VALUES (%s, %s, %s)"
            params = (nombre, sexo, correo)
            self.cursor.execute(query, params)
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            messagebox.showerror("Error al Registrar", f"No se pudo agregar el empleado: {err}")
            return False
        finally:
            self._desconectar()

    def eliminar_empleado(self, empleado_id):
        """
        Elimina un empleado de la base de datos por su ID.
        """
        if not self._conectar():
            return False
            
        try:
            # Consulta segura
            query = "DELETE FROM empleados WHERE id = %s"
            params = (empleado_id,)
            self.cursor.execute(query, params)
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            messagebox.showerror("Error al Eliminar", f"No se pudo eliminar el empleado: {err}")
            return False
        finally:
            self._desconectar()

# ============================================================
# CLASE VISTA/CONTROLADOR: Interfaz Gráfica (Tkinter)
# ============================================================
class App:
    """
    Construye y controla la interfaz gráfica de usuario.
    """
    def __init__(self, master):
        self.master = master
        master.title("Sistema de Registro de Empleados")
        master.geometry("700x500")

        # Configuración de la conexión a la base de datos
        db_config = {
            "host": "127.0.0.1",
            "user": "root",
            "password": "toor", # Cambia por tu contraseña si es necesario
            "database": "empresa_db"
        }
        self.modelo = EmpleadoModel(db_config)

        self._crear_widgets()
        self._actualizar_lista_empleados()

    def _crear_widgets(self):
        # --- Frame para el formulario de entrada ---
        form_frame = ttk.LabelFrame(self.master, text="Añadir Nuevo Empleado")
        form_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(form_frame, text="Nombre:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_nombre = ttk.Entry(form_frame, width=40)
        self.entry_nombre.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Sexo:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.combo_sexo = ttk.Combobox(form_frame, values=["Masculino", "Femenino", "Otro"], state="readonly")
        self.combo_sexo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.combo_sexo.set("Masculino") # Valor por defecto

        ttk.Label(form_frame, text="Correo:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_correo = ttk.Entry(form_frame, width=40)
        self.entry_correo.grid(row=2, column=1, padx=5, pady=5)

        btn_agregar = ttk.Button(form_frame, text="Añadir Empleado", command=self._agregar_empleado)
        btn_agregar.grid(row=3, column=0, columnspan=2, pady=10)

        # --- Frame para la lista de empleados ---
        list_frame = ttk.LabelFrame(self.master, text="Lista de Empleados")
        list_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.tree = ttk.Treeview(list_frame, columns=("ID", "Nombre", "Sexo", "Correo"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre Completo")
        self.tree.heading("Sexo", text="Sexo")
        self.tree.heading("Correo", text="Correo Electrónico")

        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Nombre", width=200)
        self.tree.column("Sexo", width=100, anchor="center")
        self.tree.column("Correo", width=200)
        
        # Scrollbar para la lista
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Frame para los botones de acción ---
        action_frame = ttk.Frame(self.master)
        action_frame.pack(pady=5)
        
        btn_eliminar = ttk.Button(action_frame, text="Eliminar Seleccionado", command=self._eliminar_empleado_seleccionado)
        btn_eliminar.pack(side="left", padx=5)
        
        btn_actualizar = ttk.Button(action_frame, text="Actualizar Lista", command=self._actualizar_lista_empleados)
        btn_actualizar.pack(side="left", padx=5)

    def _actualizar_lista_empleados(self):
        """Limpia y vuelve a cargar todos los empleados en el Treeview."""
        # Limpiar lista actual
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Obtener y mostrar empleados
        empleados = self.modelo.obtener_empleados()
        for emp in empleados:
            self.tree.insert("", "end", values=(emp['id'], emp['nombre'], emp['sexo'], emp['correo']))

    def _agregar_empleado(self):
        """Toma los datos del formulario, los valida y los envía al modelo."""
        nombre = self.entry_nombre.get().strip()
        sexo = self.combo_sexo.get()
        correo = self.entry_correo.get().strip()

        if not nombre or not correo:
            messagebox.showwarning("Campos Vacíos", "El nombre y el correo son obligatorios.")
            return

        if self.modelo.agregar_empleado(nombre, sexo, correo):
            messagebox.showinfo("Éxito", "Empleado registrado correctamente.")
            # Limpiar campos del formulario
            self.entry_nombre.delete(0, "end")
            self.entry_correo.delete(0, "end")
            self.combo_sexo.set("Masculino")
            # Actualizar la lista
            self._actualizar_lista_empleados()

    def _eliminar_empleado_seleccionado(self):
        """Elimina el empleado que está seleccionado en la lista."""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Sin Selección", "Por favor, selecciona un empleado de la lista para eliminar.")
            return

        item_seleccionado = self.tree.item(seleccion[0])
        empleado_id = item_seleccionado['values'][0]
        nombre_empleado = item_seleccionado['values'][1]

        confirmar = messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar a {nombre_empleado} (ID: {empleado_id})?")

        if confirmar:
            if self.modelo.eliminar_empleado(empleado_id):
                messagebox.showinfo("Éxito", "Empleado eliminado correctamente.")
                self._actualizar_lista_empleados()

# ============================================================
# PUNTO DE ENTRADA DE LA APLICACIÓN
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
