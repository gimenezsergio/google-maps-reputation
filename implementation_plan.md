# Plan de Implementación: Google Maps Reputation Manager

Este plan describe la arquitectura y los pasos para convertir el mockup `reputation_manager.html` en un producto SaaS profesional y mantenible.

La aplicación utilizará **FastAPI** como backend de Python, **SQLite** como base de datos, e integrará la API de **DeepSeek** para la generación de reseñas inteligentes. El frontend se estructurará con un diseño minimalista, moderno (Glassmorphism, transiciones fluidas y micro-interacciones) y adaptado a dispositivos móviles.

---

## Estructura del Proyecto

El proyecto se dividirá limpiamente entre `backend` y `frontend` en el directorio de trabajo:

```
google-maps-reputation/
├── .gitignore
├── README.md
├── backend/
│   ├── app/
│   │   ├── api/                  # Controladores y Rutas de la API (v1)
│   │   │   ├── auth.py           # Autenticación y JWT
│   │   │   ├── admin.py          # ABM de comercios para el Super Admin
│   │   │   ├── commerce.py       # Consultas y feedback para los dueños de locales
│   │   │   └── public.py         # Endpoints públicos (pantalla del QR)
│   │   ├── core/
│   │   │   ├── config.py         # Configuración y variables de entorno (.env)
│   │   │   ├── security.py       # Contraseñas y JWT
│   │   │   └── database.py       # Configuración de base de datos y sesión ORM
│   │   ├── models/               # Modelos SQLAlchemy
│   │   │   ├── commerce.py       # Modelo Comercio
│   │   │   ├── user.py           # Modelo Usuario (Roles: super_admin, commerce_admin)
│   │   │   └── feedback.py       # Modelo Comentarios Privados (1-3 estrellas)
│   │   ├── schemas/              # Validadores de datos con Pydantic
│   │   │   ├── commerce.py
│   │   │   ├── user.py
│   │   │   └── feedback.py
│   │   ├── services/             # Integraciones externas
│   │   │   └── deepseek.py       # Servicio de generación de IA
│   │   └── main.py               # Inicializador de la App FastAPI
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── css/
    │   └── custom.css            # Estilos personalizados (Glassmorphism, animaciones)
    ├── js/
    │   ├── api.js                # Cliente HTTP para llamadas al backend
    │   └── main.js               # Lógica del cliente final (pantalla del QR)
    ├── admin/                    # Panel para el Administrador de la App
    │   └── index.html
    ├── commerce/                 # Panel para el Dueño del Comercio
    │   └── index.html
    ├── opinar.html               # Pantalla principal del QR (reemplaza a reputation_manager.html)
    └── login.html                # Login unificado
```

---

## Modelo de Datos (Base de Datos SQLite)

Definiremos tres entidades principales utilizando SQLAlchemy:

### 1. `User` (Usuarios de la Plataforma)
* `id` (Integer, Primary Key)
* `username` (String, Unique, Index)
* `password_hash` (String)
* `role` (Enum: `super_admin` o `commerce_admin`)
* `commerce_id` (Integer, ForeignKey pointing to `commerce.id`, Nullable)
* `created_at` (DateTime, Default: UTC Now)

### 2. `Commerce` (Comercios registrados)
* `id` (Integer, Primary Key)
* `name` (String)
* `slug` (String, Unique, Index) - Utilizado en la URL `/opinar.html?slug=el-noble`
* `logo_url` (String, Nullable)
* `google_place_id` (String)
* `tags` (JSON/String: lista de etiquetas disponibles para este comercio)
* `is_active` (Boolean, Default: True)
* `created_at` (DateTime, Default: UTC Now)

### 3. `Feedback` (Valoraciones del cliente)
* `id` (Integer, Primary Key)
* `commerce_id` (Integer, ForeignKey pointing to `commerce.id`)
* `rating` (Integer, 1 a 5)
* `comment` (String, Nullable) - Guardado solo para calificaciones <= 3
* `created_at` (DateTime, Default: UTC Now)

---

## Flujo de Trabajo y Commits por Función

Para mantener el historial de Git limpio y modular, implementaremos el desarrollo en **10 commits funcionales e independientes**:

### 🛠️ Fase 1: Setup y Configuración Inicial
* **Cambios propuestos:**
  * Inicializar el repositorio Git dentro de `/google-maps-reputation` para desvincularlo del directorio padre.
  * Añadir `.gitignore` para omitir base de datos local SQLite, entornos virtuales y claves.
  * Crear la estructura de directorios y definir `requirements.txt`.
* **Commit 1:** `git commit -m "feat: setup inicial de estructura del proyecto y archivos de configuracion"`

### 🗄️ Fase 2: Capa de Base de Datos y Modelos
* **Cambios propuestos:**
  * Configurar `database.py` para levantar SQLite con SQLAlchemy.
  * Implementar los modelos ORM: `User`, `Commerce` y `Feedback`.
  * Crear un script inicial `init_db.py` para crear las tablas y un usuario Super Admin por defecto si no existen.
* **Commit 2:** `git commit -m "feat: definicion de modelos de base de datos y script de inicializacion"`

### 🔑 Fase 3: Seguridad y Autenticación JWT
* **Cambios propuestos:**
  * Implementar utilidades de hashing para contraseñas en `security.py`.
  * Desarrollar esquemas Pydantic para el login y el perfil de usuario.
  * Crear el router `/api/v1/auth/login` que valide credenciales y devuelva un JWT token.
* **Commit 3:** `git commit -m "feat: implementacion de autenticacion basada en JWT"`

### 🧠 Fase 4: Conector e Integración con DeepSeek API
* **Cambios propuestos:**
  * Crear el servicio de IA en `services/deepseek.py`.
  * Consumir el endpoint de chat de DeepSeek usando variables de entorno para la clave API.
  * Diseñar un prompt optimizado y estructurado (JSON de retorno con 5 variaciones de reseña).
  * Crear un fallback estático (plantilla de seguridad) en caso de caída o error en la API de DeepSeek.
* **Commit 4:** `git commit -m "feat: servicio de generacion de reseñas con IA DeepSeek"`

### 📱 Fase 5: API Pública para el Cliente Final (QR)
* **Cambios propuestos:**
  * Crear endpoints en `public.py`:
    * `GET /api/v1/public/commerce/{slug}`: Retorna nombre, logo y tags de un comercio.
    * `POST /api/v1/public/feedback`: Registra la valoración del usuario (1 a 5 estrellas y comentario privado si corresponde).
    * `POST /api/v1/public/generate-review`: Llama al servicio de DeepSeek para el comercio indicado y retorna las 5 opciones de reseña.
* **Commit 5:** `git commit -m "feat: endpoints publicos de la API para el cliente final (QR)"`

### 👑 Fase 6: API del Super Admin
* **Cambios propuestos:**
  * Desarrollar endpoints protegidos en `admin.py`:
    * `POST /api/v1/admin/commerce`: Crea un nuevo comercio y su usuario administrador asignado.
    * `GET /api/v1/admin/commerces`: Lista todos los comercios y sus métricas globales básicas.
    * `PUT /api/v1/admin/commerce/{id}`: Modifica datos, logo o tags de un comercio.
    * `DELETE /api/v1/admin/commerce/{id}`: Desactiva o elimina un comercio.
* **Commit 6:** `git commit -m "feat: endpoints de administracion global (Super Admin)"`

### 📈 Fase 7: API del Administrador del Comercio
* **Cambios propuestos:**
  * Crear endpoints protegidos en `commerce.py`:
    * `GET /api/v1/commerce/feedbacks`: Lista los comentarios privados recibidos (1-3 estrellas) para el comercio del usuario logueado.
    * `GET /api/v1/commerce/stats`: Devuelve las métricas de rendimiento (rating promedio, total opiniones, frecuencia de uso de etiquetas).
* **Commit 7:** `git commit -m "feat: endpoints de estadisticas y feedback para administradores de comercio"`

### 🎨 Fase 8: Frontend del Cliente Final (QR)
* **Cambios propuestos:**
  * Reestructurar `opinar.html` (reemplazando la lógica de Firebase del mockup por llamadas a nuestra API pública).
  * Consumir dinámicamente los tags y datos del comercio leyendo el parámetro `slug` de la URL.
  * Incorporar una interfaz pulida y limpia (micro-animaciones en estrellas, carga fluida, popover instructivo de "Cómo pegar").
* **Commit 8:** `git commit -m "feat: frontend minimalista y responsivo para el cliente final (QR)"`

### 🖥️ Fase 9: Frontend de los Dashboards y Autenticación
* **Cambios propuestos:**
  * Crear `login.html` que guarde el token JWT en `localStorage`.
  * Desarrollar el Dashboard de Super Admin (`admin/index.html`): Formulario de creación de comercios, lista de comercios registrados y asignación de tags.
  * Desarrollar el Dashboard del Comercio (`commerce/index.html`): Listado de feedback de contención (1-3 estrellas) y sección de analíticas simples.
* **Commit 9:** `git commit -m "feat: interfaces web para login, dashboard de super admin y dashboard de comercio"`

### ✨ Fase 10: Pulido de UI/UX (Wow Factor) y Pruebas
* **Cambios propuestos:**
  * Añadir efectos visuales premium (Glassmorphism en tarjetas de feedback, transiciones elegantes usando CSS y View Transitions, gradientes estéticos).
  * Validar toda la experiencia móvil.
  * Realizar pruebas de extremo a extremo (registro de comercio, simulación de escaneo QR, envío de feedback negativo, generación de reseñas DeepSeek exitosa).
* **Commit 10:** `git commit -m "design: pulido final estetico, transiciones y validacion general de UI/UX"`

---

## Plan de Verificación

Para garantizar que el sistema funcione perfectamente:

1. **Pruebas Manuales de Flujo Completo:**
   * **Caso A (Cliente Satisfecho):** Ingresar a `/opinar.html?slug=test`, calificar con 5 estrellas, elegir etiquetas, presionar generar reseñas, verificar que DeepSeek responda adecuadamente y que el botón de copiar funcione abriendo Google Maps con el Place ID cargado.
   * **Caso B (Cliente Insatisfecho):** Calificar con 2 estrellas, verificar la redirección a la pantalla de contención, redactar comentario privado, enviarlo y confirmar que no redirija a Google Maps.
   * **Caso C (Paneles Administrativos):**
     * Loguearse como Super Admin, crear un comercio de prueba, definir sus tags, verificar su almacenamiento en la DB SQLite.
     * Loguearse como el administrador de ese comercio de prueba, verificar que se visualice la queja del Caso B y las métricas actualizadas de satisfacción.
2. **Seguridad de API:**
   * Validar que los endpoints protegidos bajo `/api/v1/admin/*` y `/api/v1/commerce/*` denieguen el acceso si no se provee un token JWT válido o si el rol no coincide.
   * Verificar que la API de DeepSeek solo sea accesible a través del backend.
