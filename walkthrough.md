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

### Paso 1: Registro del Comercio (Super Admin)
1. Abre [http://localhost:8000/login.html](http://localhost:8000/login.html) en tu navegador.
2. Ingresa con las credenciales de Super Admin (`admin` / `admin123`).
3. Serás redirigido al panel global de Super Admin.
4. En el formulario de la izquierda, registra un comercio:
   * **Nombre:** `La Querencia Parrilla`
   * **Slug:** `la-querencia`
   * **Google Place ID:** `ChIJN1t_tDeuEmsRUsoyG83frY4` *(Place ID de prueba)*
   * **URL del Logotipo:** Puedes dejarlo vacío o pegar una URL de imagen pública.
   * **Etiquetas:** `Carne tierna, Servicio rápido, Excelente ambiente, Precios justos, Mozo amable`
   * **Usuario de Acceso:** `querencia_admin`
   * **Contraseña de Acceso:** `querencia123`
5. Presiona **Guardar Comercio**. Verás que aparece inmediatamente en la lista de la derecha.

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
