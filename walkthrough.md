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

### Paso 5: Generación y Uso de Códigos QR (Dinámicos)
1. **En el panel de Super Admin**:
   * Al crear un nuevo comercio, verás el código QR público renderizado dinámicamente en el modal de éxito junto con las credenciales.
   * En la lista de comercios registrados, haz clic en el botón **Ver QR** de cualquier local.
   * Se abrirá un modal premium que muestra el QR. Prueba el botón **Descargar** para bajar el archivo PNG o **Imprimir** para generar una página limpia lista para impresión.
2. **En el panel de Comercio (Dueño)**:
   * Inicia sesión con la cuenta de un local (ej. `querencia_admin`).
   * En la barra de navegación superior, haz clic en el botón **Ver QR**.
   * Se abrirá el modal con el QR de tu local, apuntando automáticamente al dominio actual de tu despliegue. También puedes descargarlo o imprimirlo desde aquí.

---

## Archivos de Configuración del Servidor

* Las variables de entorno locales están definidas en [backend/.env](file:///home/sergio/Documents/src/google-maps-reputation/backend/.env).
* Si deseas habilitar la generación de reseñas con DeepSeek en producción, simplemente agrega tu clave de API en la variable `DEEPSEEK_API_KEY` de ese archivo y reinicia el servidor.

---

## Validación de Enlaces de Google Maps (Fase 13)

Hemos añadido un sistema de validación robusto en la carga automática de enlaces para evitar errores 404 al intentar dejar valoraciones en fichas inexistentes.

### Comportamiento de Bloqueo
El sistema bloqueará las siguientes URLs y retornará un error `HTTP 400 Bad Request`:
1. **Puntos Geográficos y Coordenadas Puras**: URLs como `https://www.google.com/maps/place/-34.654877,-58.5029416` o que incluyan únicamente números decimales como nombre.
2. **Puntos y Calles del Mapa**: URLs que no corresponden a un comercio y contienen la estructura interna de coordenadas de Google Maps (ej. `/maps/place/data=!4m2!3m1!1s...` con título genérico `"Google Maps"`).
3. **Páginas de Búsqueda Genérica**: Enlaces donde el nombre resuelto sea `"Comercio"` o `"Google Maps"` sin una ficha de negocio asignada.

### Mensaje de Error (Toast)
Al pegar un enlace de este tipo y presionar **Cargar**, el sistema mostrará un Toast rojo en la esquina inferior derecha informando:
> *"El enlace ingresado corresponde a un punto en el mapa o a coordenadas geográficas, no a la ficha de un comercio. Por favor, busca el comercio en Google Maps, haz clic en Compartir y copia ese enlace."*

### Cómo Probarlo
1. Ve a [http://localhost:8000/login.html](http://localhost:8000/login.html) e ingresa como Super Admin.
2. Intenta ingresar la siguiente URL de coordenadas en el campo de Carga Automática:
   `https://www.google.com/maps/place/data=!4m2!3m1!1s0x95bcc90090613b5b:0x2cf80e7955abf453?hl=es`
3. Presiona **Cargar**. Deberías ver un toast rojo indicando que la URL corresponde a un punto geográfico o coordenadas.
4. Ahora, intenta ingresar una URL comercial válida, como la de *Café de la Plaza*:
   `https://www.google.com/maps/place/Caf%C3%A9+de+la+Plaza/@-34.5721111,-58.4556667,17z/data=!3m1!4b1!4m6!3m5!1s0x95bcb59b7dfb3d37:0x2c64e622ef5159b9!8m2!3d-34.5721111!4d-58.4556667!16s%2Fg%2F11b77m_jpy?entry=ttu`
5. Presiona **Cargar**. Los datos de Café de la Plaza se cargarán exitosamente sin ningún error.


