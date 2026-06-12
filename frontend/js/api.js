// Resolve the app base path so the frontend works both at / and under a subroute.
const APP_BASE_PATH = (() => {
    const path = window.location.pathname;
    const markers = ["/admin/", "/commerce/", "/login.html", "/opinar.html"];

    for (const marker of markers) {
        const idx = path.indexOf(marker);
        if (idx !== -1) {
            return `${path.slice(0, idx)}/`;
        }
    }

    const lastSlash = path.lastIndexOf("/");
    return lastSlash >= 0 ? path.slice(0, lastSlash + 1) : "/";
})();

function appUrl(relativePath = "") {
    return new URL(relativePath, `${window.location.origin}${APP_BASE_PATH}`).toString();
}

// Client API configuration
const API_BASE_URL = appUrl("api/v1").replace(/\/$/, "");

const API = {
    // PUBLIC API ENDPOINTS
    async getCommerce(slug) {
        const response = await fetch(`${API_BASE_URL}/public/commerce/${slug}`);
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Error al obtener la información del comercio");
        }
        return response.json();
    },

    async submitFeedback(slug, rating, comment = null, tags = [], customer_email = null) {
        const response = await fetch(`${API_BASE_URL}/public/commerce/${slug}/feedback`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ rating, comment, tags, customer_email })
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Error al enviar el feedback");
        }
        return response.json();
    },

    async generateReview(slug, tags) {
        const response = await fetch(`${API_BASE_URL}/public/commerce/${slug}/generate-review`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(tags)
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Error al generar la reseña");
        }
        return response.json();
    },

    // AUTH API ENDPOINTS
    async login(username, password) {
        const params = new URLSearchParams();
        params.append("username", username);
        params.append("password", password);

        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: params
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Credenciales incorrectas");
        }
        return response.json();
    },

    async getMe(token) {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });
        if (!response.ok) {
            throw new Error("Token inválido");
        }
        return response.json();
    },

    // SUPER ADMIN ENDPOINTS
    async createCommerce(token, commerceData) {
        const response = await fetch(`${API_BASE_URL}/admin/commerce`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(commerceData)
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Error al crear el comercio");
        }
        return response.json();
    },

    async getCommerces(token) {
        const response = await fetch(`${API_BASE_URL}/admin/commerces`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });
        if (!response.ok) {
            throw new Error("Error al obtener los comercios");
        }
        return response.json();
    },

    async updateCommerce(token, id, commerceData) {
        const response = await fetch(`${API_BASE_URL}/admin/commerce/${id}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(commerceData)
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Error al actualizar el comercio");
        }
        return response.json();
    },

    async deleteCommerce(token, id) {
        const response = await fetch(`${API_BASE_URL}/admin/commerce/${id}`, {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });
        if (!response.ok) {
            throw new Error("Error al eliminar el comercio");
        }
        return response.json();
    },

    async searchPlaces(token, q) {
        const response = await fetch(`${API_BASE_URL}/admin/search-places?q=${encodeURIComponent(q)}`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Error al buscar comercios en Google Maps");
        }
        return response.json();
    },

    // COMMERCE ADMIN ENDPOINTS
    async getMyCommerce(token) {
        const response = await fetch(`${API_BASE_URL}/commerce/my-commerce`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Error al obtener detalles del comercio");
        }
        return response.json();
    },

    async getFeedbacks(token) {
        const response = await fetch(`${API_BASE_URL}/commerce/feedbacks`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });
        if (!response.ok) {
            throw new Error("Error al obtener opiniones");
        }
        return response.json();
    },

    async getStats(token) {
        const response = await fetch(`${API_BASE_URL}/commerce/stats`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });
        if (!response.ok) {
            throw new Error("Error al obtener estadísticas");
        }
        return response.json();
    }
};

window.API = API;
window.APP_BASE_PATH = APP_BASE_PATH;
window.appUrl = appUrl;
