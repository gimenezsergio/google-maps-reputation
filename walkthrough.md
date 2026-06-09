# Guía de Verificación: Google Maps Reputation Manager

¡Felicitaciones! Hemos implementado de forma completa y robusta la aplicación siguiendo el plan acordado. La base de código cuenta con **10 commits granulares e independientes**, organizados por función, y está 100% libre de código temporal o de Firebase.

El servidor web y la API ya se encuentran **ejecutándose en segundo plano en `http://localhost:8000`**.

---

## Estructura de Credenciales de Prueba

Para realizar las verificaciones, utiliza los siguientes accesos:

| Rol | URL de Acceso | Usuario | Contraseña |
| :--- | :--- | :--- | :--- |
| **Super Administrador** | [login.html](http://localhost:8000/login.html) | `admin` | `admin123` |
| **Administrador de Local** | [login.html](http://localhost:8000/login.html) | *Configurado en el panel* | *Configurado en el panel* |

---

## Pasos para la Verificación Completa (Flujo End-to-End)

Sigue estos pasos para probar todas las funcionalidades:

### Paso 1: Registro del Comercio con Enlace de Google Maps (Super Admin)
1. Abre [http://localhost:8000/login.html](http://localhost:8000/login.html) en tu navegador.
2. Ingresa con las credenciales de Super Admin (`admin` / `admin123`).
3. Serás redirigido al panel global de Super Admin.
4. En el formulario de la izquierda, verás el campo **Enlace de Google Maps (Carga Automática)**.
5. Pega un enlace de Google Maps o un enlace corto compartido (ej. `https://maps.app.goo.gl/u2g3N7yH2MvM9m8s6` o un link con formato `0x...:0x...`).
6. Presiona **Cargar**. La aplicación resolverá el redireccionamiento, extraerá el Nombre y el Place ID (soportando tanto FIDs hexadecimales `0x...` como Place IDs estándar `ChIJ...`), y auto-completará:
   * **Nombre Comercial** (ej. *Café de la Plaza*).
   * **Dynamic Slug** (ej. *cafe-de-la-plaza*).
   * **Google Place ID** (ej. *0x95bcb59b7dfb3d37:0x2c64e622ef5159b9*).
   * **URL del Logotipo** (obtenido automáticamente de imágenes curadas de Unsplash según su categoría/rubro).
   * **Etiquetas** por defecto.
   * **Credenciales del local** autogeneradas de forma segura (usuario `slug_admin` y clave aleatoria fuerte).
7. Revisa los datos (puedes editarlos en el formulario si es necesario) y haz clic en **Guardar Comercio**.
8. Se guardará el comercio y se mostrará un modal con las credenciales generadas y un botón para **Copiar Datos** al portapapeles.
9. El nuevo comercio se listará inmediatamente en la tabla derecha.

---

### Paso 2: Flujo de Cliente Satisfecho (QR / Pantalla Pública)
1. Entra a la URL del cliente para el local recién creado: [http://localhost:8000/opinar.html?slug=la-querencia](http://localhost:8000/opinar.html?slug=la-querencia).
2. Selecciona una calificación de **5 estrellas**.
3. Selecciona las etiquetas destacadas (ej. `Carne tierna`, `Mozo amable`).
4. Haz clic en **Generar mi reseña con IA**.
   * *Nota:* Si no has configurado tu clave `DEEPSEEK_API_KEY` en el archivo `.env`, la aplicación cargará automáticamente plantillas de contingencia personalizadas de forma inmediata y sin fallos.
5. Elige una de las reseñas generadas por la IA para copiarla en el portapapeles.
6. El sistema te redirigirá a la pantalla de opiniones de Google Maps de ese comercio para que pegues el texto.

---

### Paso 3: Flujo de Cliente Insatisfecho (Contención)
1. Vuelve a entrar a [http://localhost:8000/opinar.html?slug=la-querencia](http://localhost:8000/opinar.html?slug=la-querencia).
2. Selecciona una calificación de **2 estrellas**.
3. Serás redirigido a la pantalla privada de contención de reclamos.
4. Escribe una queja (ej. *"La mesa tardó 40 minutos y la comida llegó fría"*).
5. Presiona **Enviar comentario privado**. La queja se guardará de forma segura en la base de datos de tu servidor.

---

### Paso 4: Monitoreo y Analíticas (Dashboard del Comercio)
1. Ve a [http://localhost:8000/login.html](http://localhost:8000/login.html) (si estás logueado como Super Admin, presiona cerrar sesión primero).
2. Ingresa con las credenciales de comercio que creaste en el Paso 1 (`querencia_admin` / `querencia123`).
3. Accederás al panel privado de analíticas de **La Querencia Parrilla**.
4. Podrás verificar:
   * Las estadísticas generales actualizadas (2 valoraciones totales, promedio 3.5 estrellas).
   * La lista de comentarios privados de contención (verás la queja de las 2 estrellas escrita en el Paso 3 con su fecha exacta).
   * Un gráfico de barras con la distribución de estrellas dadas.
   * La nube de etiquetas más valoradas por tus clientes satisfechos.

---

## Archivos de Configuración del Servidor

* Las variables de entorno locales están definidas en [backend/.env](file:///home/sergio/Documents/src/google-maps-reputation/backend/.env).
* Si deseas habilitar la generación de reseñas con DeepSeek en producción, simplemente agrega tu clave de API en la variable `DEEPSEEK_API_KEY` de ese archivo y reinicia el servidor.
