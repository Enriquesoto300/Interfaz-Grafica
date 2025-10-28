import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
import csv
import random
from PIL import Image, ImageTk
import os # Importación clave

# ============================================================
# CLASE MODELO: Gestión de la Lógica de Negocio y Base de Datos
# ============================================================
class EmpleadoModel:
    """
    Se encarga de toda la comunicación con la base de datos MySQL.
    La conexión ahora se mantiene abierta mientras la app se ejecuta.
    """
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        self._conectar()

    def _conectar(self):
        """Establece la conexión con la base de datos."""
        try:
            if self.connection and self.connection.is_connected():
                self._desconectar()
            self.connection = mysql.connector.connect(**self.db_config)
            self.cursor = self.connection.cursor(dictionary=True)
            return True
        except mysql.connector.Error as err:
            self.connection = None
            self.cursor = None
            messagebox.showerror("Error de Conexión", f"No se pudo conectar a la base de datos: {err}")
            return False

    def _desconectar(self):
        """Cierra la conexión con la base de datos."""
        if self.connection and self.connection.is_connected():
            if self.cursor:
                self.cursor.close()
            self.connection.close()
            
    def cerrar_conexion_final(self):
        """Método público para cerrar la conexión al salir de la app."""
        self._desconectar()

    def _verificar_conexion(self):
        """
        Verifica si la conexión está activa y reconecta si es necesario.
        """
        try:
            if not self.connection or not self.connection.is_connected():
                if not self._conectar(): 
                    return False 
                return True 

            self.connection.ping(reconnect=True, attempts=1, delay=0)
            
            # Re-creamos el cursor para asegurar que es válido después del ping
            self.cursor = self.connection.cursor(dictionary=True)
            return True
            
        except mysql.connector.Error as err:
            messagebox.showwarning("Conexión Perdida", f"Se perdió la conexión a la BD: {err}. Reconectando...")
            if not self._conectar(): 
                messagebox.showerror("Fallo de Reconexión", "No se pudo restablecer la conexión.")
                return False
            return True 

    def obtener_empleados(self):
        """Recupera todos los empleados de la base de datos."""
        if not self._verificar_conexion():
            return []
        
        try:
            self.cursor.execute("SELECT id, nombre, sexo, correo FROM empleados ORDER BY id")
            empleados = self.cursor.fetchall()
            return empleados
        except mysql.connector.Error as err:
            messagebox.showerror("Error de Consulta", f"No se pudo obtener la lista de empleados: {err}")
            return []

    def agregar_empleado(self, nombre, sexo, correo):
        """Agrega un nuevo empleado (Seguro contra Inyección SQL)."""
        if not self._verificar_conexion():
            return False
                
        try:
            query = "INSERT INTO empleados (nombre, sexo, correo) VALUES (%s, %s, %s)"
            params = (nombre, sexo, correo)
            self.cursor.execute(query, params)
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            messagebox.showerror("Error al Registrar", f"No se pudo agregar el empleado: {err}")
            return False

    def eliminar_empleado(self, empleado_id):
        """Elimina un empleado por su ID (Seguro contra Inyección SQL)."""
        if not self._verificar_conexion():
            return False
                
        try:
            query = "DELETE FROM empleados WHERE id = %s"
            params = (empleado_id,)
            self.cursor.execute(query, params)
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            messagebox.showerror("Error al Eliminar", f"No se pudo eliminar el empleado: {err}")
            return False

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
        self.ancho_ventana = 900
        self.alto_ventana = 700
        master.geometry(f"{self.ancho_ventana}x{self.alto_ventana}")
        master.resizable(False, False)

        # --- LA SOLUCIÓN DEFINITIVA A LAS RUTAS ---
        script_path = os.path.abspath(__file__)
        self.base_dir = os.path.dirname(script_path)
        self.path_fondo = os.path.join(self.base_dir, "darksouls.PNG")
        self.path_gif = os.path.join(self.base_dir, "saludo_animado.gif")
        # --- FIN DE LA SOLUCIÓN ---

        # Configuración de la conexión a la base de datos
        db_config = {
            "host": "127.0.0.1",
            "user": "root",
            "password": "toor", # Cambia por tu contraseña
            "database": "empresa_db"
        }
        self.modelo = EmpleadoModel(db_config)
        
        self.gif_frames = []
        self.gif_frame_index = 0
        self.gif_label = None
        self.gif_window = None

        self._cargar_fondo()
        self._crear_estilos_ttk()
        self._crear_widgets()
        self._actualizar_lista_empleados()
        
        master.protocol("WM_DELETE_WINDOW", self._al_cerrar_app)

    def _cargar_fondo(self):
        """
        Carga la imagen de fondo desde la ruta absoluta (self.path_fondo).
        """
        try:
            if not os.path.exists(self.path_fondo):
                raise FileNotFoundError(f"No se encontró el archivo en la ruta: {self.path_fondo}")

            img = Image.open(self.path_fondo)
            img = img.resize((self.ancho_ventana, self.alto_ventana), Image.LANCZOS)
            self.fondo_tk = ImageTk.PhotoImage(img)
            
            self.canvas_fondo = tk.Label(self.master, image=self.fondo_tk)
            self.canvas_fondo.place(x=0, y=0, relwidth=1, relheight=1)
            
        except Exception as e:
            print(f"Error al cargar imagen de fondo: {e}")
            messagebox.showerror("Error de Imagen", f"No se pudo cargar el fondo.\nError: {e}\n\nAsegúrate de que el archivo existe y el nombre es correcto.")
            self.master.configure(bg="#2b2b2b")

    def _crear_estilos_ttk(self):
        """Define los estilos personalizados para los botones."""
        style = ttk.Style()
        style.theme_use('clam')
        self.pixel_font = ("Consolas", 11, "bold")

        style.configure("Dark.TLabelframe", background="#3c3c3c", foreground="#e0e0e0", font=self.pixel_font)
        style.configure("Dark.TLabelframe.Label", background="#3c3c3c", foreground="#e0e0e0", font=self.pixel_font)
        style.configure("Dark.TLabel", background="#3c3c3c", foreground="#e0e0e0", font=self.pixel_font)
        style.configure("Dark.TEntry", fieldbackground="#555555", foreground="#ffffff", insertcolor="#ffffff", font=self.pixel_font)
        style.map("Dark.TCombobox",
                    fieldbackground=[('readonly', '#555555')],
                    foreground=[('readonly', '#ffffff')],
                    selectbackground=[('readonly', '#0078d7')],
                    selectforeground=[('readonly', '#ffffff')])
        style.configure("Dark.TCombobox", font=self.pixel_font)
        
        # Estilos de Botones
        # Usamos un background un poco transparente si el fondo es oscuro para que "flote" mejor.
        # En TTK, el background directo en configure no admite transparencia alpha.
        # Una alternativa sería usar un Canvas o un Frame con una imagen semi-transparente como fondo
        # para cada botón, pero eso es más complejo. Por ahora, un color sólido que contraste o se integre.
        # Mantendré los colores definidos, pero imagina que "flotan" por su contraste.
        style.configure("Add.TButton", background="#28a745", foreground="white", font=self.pixel_font, padding=10, relief="raised", bordercolor="#28a745")
        style.map("Add.TButton", background=[('active', '#218838'), ('hover', '#34ce57')], relief=[('hover', 'sunken'), ('!hover', 'raised')])
        style.configure("Delete.TButton", background="#dc3545", foreground="white", font=self.pixel_font, padding=10, relief="raised", bordercolor="#dc3545")
        style.map("Delete.TButton", background=[('active', '#c82333'), ('hover', '#e4606d')], relief=[('hover', 'sunken'), ('!hover', 'raised')])
        style.configure("Update.TButton", background="#007bff", foreground="white", font=self.pixel_font, padding=10, relief="raised", bordercolor="#007bff")
        style.map("Update.TButton", background=[('active', '#0069d9'), ('hover', '#3395ff')], relief=[('hover', 'sunken'), ('!hover', 'raised')])
        style.configure("Hack.TButton", background="#fd7e14", foreground="black", font=self.pixel_font, padding=10, relief="raised", bordercolor="#fd7e14")
        style.map("Hack.TButton", background=[('active', '#e86a02'), ('hover', '#ff9a40')], relief=[('hover', 'sunken'), ('!hover', 'raised')])
        style.configure("Fun.TButton", background="#ffc107", foreground="black", font=self.pixel_font, padding=10, relief="raised", bordercolor="#ffc107")
        style.map("Fun.TButton", background=[('active', '#e0a800'), ('hover', '#ffd241')], relief=[('hover', 'sunken'), ('!hover', 'raised')])
        
        # Estilo Treeview
        style.configure("Treeview", background="#3c3c3c", fieldbackground="#3c3c3c", foreground="#e0e0e0", font=("Consolas", 10))
        style.configure("Treeview.Heading", background="#555555", foreground="#ffffff", font=self.pixel_font, relief="raised")
        style.map("Treeview.Heading", background=[('active', '#666666')])

    def _crear_widgets(self):
        
        # Frame Formulario (apilado a la izquierda)
        form_frame = ttk.LabelFrame(self.master, text="Añadir Nuevo Empleado", style="Dark.TLabelframe")
        form_frame.place(x=20, y=20, width=420, height=220)
        
        ttk.Label(form_frame, text="Nombre:", style="Dark.TLabel").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_nombre = ttk.Entry(form_frame, width=38, style="Dark.TEntry")
        self.entry_nombre.grid(row=0, column=1, padx=10, pady=10)
        ttk.Label(form_frame, text="Sexo:", style="Dark.TLabel").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.combo_sexo = ttk.Combobox(form_frame, values=["Masculino", "Femenino", "Otro"], state="readonly", style="Dark.TCombobox", width=36)
        self.combo_sexo.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.combo_sexo.set("Masculino") 
        ttk.Label(form_frame, text="Correo:", style="Dark.TLabel").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.entry_correo = ttk.Entry(form_frame, width=38, style="Dark.TEntry")
        self.entry_correo.grid(row=2, column=1, padx=10, pady=10)
        btn_agregar = ttk.Button(form_frame, text="Añadir Empleado", command=self._agregar_empleado, style="Add.TButton")
        btn_agregar.grid(row=3, column=0, columnspan=2, pady=15)

        # Frame Lista (apilado a la izquierda, debajo del formulario)
        list_frame = ttk.LabelFrame(self.master, text="Lista de Empleados", style="Dark.TLabelframe")
        # Ahora empieza en y=250 porque no hay action_frame encima
        list_frame.place(x=20, y=250, width=420, height=420) # Aumento de altura para ocupar más espacio

        self.tree = ttk.Treeview(list_frame, columns=("ID", "Nombre", "Sexo", "Correo"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre Completo")
        self.tree.heading("Sexo", text="Sexo")
        self.tree.heading("Correo", text="Correo Electrónico")
        
        # Anchos de columna ajustados para caber en 420px
        self.tree.column("ID", width=30, anchor="center")
        self.tree.column("Nombre", width=120)
        self.tree.column("Sexo", width=70, anchor="center")
        self.tree.column("Correo", width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5, padx=(0,5))

        # === Botones "flotantes" sobre el fondo ===
        # Los posicionamos directamente en self.master, en la parte superior derecha.
        # Ajusta las coordenadas (x, y) según quieras que queden.
        
        btn_eliminar = ttk.Button(self.master, text="Eliminar Seleccionado", command=self._eliminar_empleado_seleccionado, style="Delete.TButton")
        btn_eliminar.place(x=480, y=30, width=200) # x=480 para dejar margen a la izquierda
        
        btn_actualizar = ttk.Button(self.master, text="Actualizar Lista", command=self._actualizar_lista_empleados, style="Update.TButton")
        btn_actualizar.place(x=480, y=90, width=200) # Debajo del botón eliminar
        
        btn_hackear = ttk.Button(self.master, text="Hackear Ilegalmente la Base de Datos", command=self._exportar_a_csv, style="Hack.TButton")
        btn_hackear.place(x=480, y=150, width=350) # Más ancho
        
        btn_mensaje = ttk.Button(self.master, text="Click aquí para mensaje interesante", command=self._mostrar_ventana_gif, style="Fun.TButton")
        btn_mensaje.place(x=480, y=210, width=350) # Debajo del botón hackear

        # Botón Fugitivo (Sin cambios)
        self.btn_cerrar_fugitivo = tk.Button(self.master, text="Cerrar", command=self._al_cerrar_app, bg="#dc3545", fg="white", font=("Consolas", 10, "bold"), relief="raised", borderwidth=3)
        self.btn_cerrar_fugitivo.place(x=self.ancho_ventana - 80, y=self.alto_ventana - 50)
        self.btn_cerrar_fugitivo.bind("<Enter>", self._mover_boton_cerrar)

    def _actualizar_lista_empleados(self):
        """Limpia y vuelve a cargar todos los empleados en el Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        empleados = self.modelo.obtener_empleados()
        if empleados: 
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
            self.entry_nombre.delete(0, "end")
            self.entry_correo.delete(0, "end")
            self.combo_sexo.set("Masculino")
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
                
    def _al_cerrar_app(self):
        """Función personalizada para el cierre de la app."""
        if messagebox.askokcancel("Salir", "¿Seguro que quieres salir?"):
            print("Cerrando conexión a la base de datos...")
            self.modelo.cerrar_conexion_final()
            self.master.destroy()

    # --- Funciones de los nuevos botones ---

    def _exportar_a_csv(self):
        """(Broma 'Hackear') Exporta todos los empleados a un archivo CSV."""
        empleados = self.modelo.obtener_empleados()
        if not empleados:
            messagebox.showinfo("Exportar CSV", "No hay empleados para exportar.")
            return
        
        # Construye la ruta de guardado en la misma carpeta del script
        filename = os.path.join(self.base_dir, "empleados_exportados_ilegalmente.csv")
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = empleados[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for emp in empleados:
                    writer.writerow(emp)
            
            messagebox.showinfo("¡¡Hackeo Exitoso!!", 
                                f"¡Base de datos hackeada!\nLos datos se han exfiltrado a:\n{filename}")
        except Exception as e:
            messagebox.showerror("¡Fallo del Hackeo!", f"No se pudo completar la exfiltración: {e}")

    def _mostrar_ventana_gif(self):
        """
        Abre una nueva ventana (Toplevel) y muestra un GIF animado desde la ruta absoluta.
        """
        if self.gif_window and self.gif_window.winfo_exists():
            self.gif_window.lift() 
            return
            
        self.gif_window = tk.Toplevel(self.master)
        self.gif_window.title("Hola Mundo")
        self.gif_window.geometry("300x300")
        self.gif_window.configure(bg="#2b2b2b")

        try:
            if not os.path.exists(self.path_gif):
                raise FileNotFoundError(f"No se encontró el archivo en la ruta: {self.path_gif}")

            gif_image = Image.open(self.path_gif)
            
            self.gif_frames = []
            for i in range(gif_image.n_frames):
                gif_image.seek(i)
                frame = gif_image.copy().convert("RGBA")
                self.gif_frames.append(ImageTk.PhotoImage(frame))
                
            self.gif_frame_index = 0
            
            if not self.gif_label:
                self.gif_label = tk.Label(self.gif_window, bg="#2b2b2b")
                self.gif_label.pack(expand=True, fill="both")
            else:
                self.gif_label.configure(master=self.gif_window)
            
            self._animar_gif()
            
        except Exception as e:
            print(f"Error al cargar GIF: {e}")
            messagebox.showerror("Error de GIF", f"No se pudo cargar el mensaje.\nError: {e}\n\nAsegúrate de que el archivo existe y el nombre es correcto.")
            self.gif_window.destroy()

    def _animar_gif(self):
        """Ciclo de animación para el GIF."""
        if not self.gif_window or not self.gif_window.winfo_exists():
            return 

        frame_actual = self.gif_frames[self.gif_frame_index]
        self.gif_label.config(image=frame_actual)
        
        self.gif_frame_index += 1
        if self.gif_frame_index >= len(self.gif_frames):
            self.gif_frame_index = 0 
            
        self.gif_window.after(100, self._animar_gif)

    def _mover_boton_cerrar(self, event):
        """Mueve el botón 'Cerrar' a una posición aleatoria."""
        max_x = self.ancho_ventana - self.btn_cerrar_fugitivo.winfo_width() - 10
        max_y = self.alto_ventana - self.btn_cerrar_fugitivo.winfo_height() - 10
        
        nuevo_x = random.randint(10, max_x)
        nuevo_y = random.randint(10, max_y)
        
        self.btn_cerrar_fugitivo.place(x=nuevo_x, y=nuevo_y)

# ============================================================
# PUNTO DE ENTRADA DE LA APLICACIÓN
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()