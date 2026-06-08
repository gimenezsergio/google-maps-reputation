// State Management for customer feedback flow
let state = {
    step: 'loading',
    rating: 0,
    selectedTags: [],
    aiResults: [],
    commerce: null,
    slug: '',
    loading: false
};

// Initialize app on load
document.addEventListener("DOMContentLoaded", async () => {
    const params = new URLSearchParams(window.location.search);
    state.slug = params.get('slug') || params.get('id');

    if (!state.slug) {
        showError("Falta el identificador del comercio en la URL (ej. ?slug=nombre)");
        return;
    }

    try {
        state.commerce = await API.getCommerce(state.slug);
        state.step = 'rating';
        render();
    } catch (e) {
        showError(e.message || "Error al cargar la experiencia de valoración");
    }
});

function showError(msg) {
    const container = document.getElementById('screen-container');
    container.innerHTML = `
        <div class="text-center py-8">
            <div class="inline-flex items-center justify-center w-16 h-16 bg-red-100 text-red-500 rounded-full mb-4 text-3xl">✕</div>
            <h2 class="text-xl font-semibold text-gray-800 mb-2">Ups, ocurrió un problema</h2>
            <p class="text-sm text-gray-500 px-4">${msg}</p>
        </div>
    `;
}

function render() {
    const container = document.getElementById('screen-container');
    
    // Update logo/name if commerce is loaded
    const logoImg = document.getElementById('commerce-logo');
    const commerceNameText = document.getElementById('commerce-name');
    if (state.commerce) {
        commerceNameText.innerText = state.commerce.name;
        if (state.commerce.logo_url) {
            logoImg.src = state.commerce.logo_url;
            logoImg.classList.remove('hidden');
            document.getElementById('logo-placeholder').classList.add('hidden');
        } else {
            logoImg.classList.add('hidden');
            document.getElementById('logo-placeholder').classList.remove('hidden');
            document.getElementById('logo-initial').innerText = state.commerce.name.charAt(0).toUpperCase();
        }
    }

    if (state.loading) {
        container.innerHTML = `
            <div class="flex flex-col items-center py-12">
                <div class="relative flex items-center justify-center">
                    <div class="animate-spin rounded-full h-14 w-14 border-b-2 border-indigo-600"></div>
                    <div class="absolute text-indigo-600 font-semibold text-xs">AI</div>
                </div>
                <p class="text-gray-500 text-sm mt-6 text-center animate-pulse">
                    ${state.step === 'ai' ? 'DeepSeek está redactando tus opciones de reseña...' : 'Procesando...'}
                </p>
            </div>
        `;
        return;
    }

    switch(state.step) {
        case 'rating':
            container.innerHTML = `
                <div class="text-center">
                    <h2 class="text-2xl font-bold text-gray-800 mb-2">¡Hola!</h2>
                    <p class="text-gray-500 text-sm mb-8">¿Cómo calificarías tu experiencia hoy?</p>
                    <div class="flex justify-center space-x-2 star-rating mb-8" style="direction: rtl;">
                        <input type="radio" id="star5" name="rating" value="5" class="hidden" /><label for="star5" onclick="setRating(5)" class="text-gray-300 text-4xl cursor-pointer hover:text-amber-400 transition-colors duration-150">★</label>
                        <input type="radio" id="star4" name="rating" value="4" class="hidden" /><label for="star4" onclick="setRating(4)" class="text-gray-300 text-4xl cursor-pointer hover:text-amber-400 transition-colors duration-150">★</label>
                        <input type="radio" id="star3" name="rating" value="3" class="hidden" /><label for="star3" onclick="setRating(3)" class="text-gray-300 text-4xl cursor-pointer hover:text-amber-400 transition-colors duration-150">★</label>
                        <input type="radio" id="star2" name="rating" value="2" class="hidden" /><label for="star2" onclick="setRating(2)" class="text-gray-300 text-4xl cursor-pointer hover:text-amber-400 transition-colors duration-150">★</label>
                        <input type="radio" id="star1" name="rating" value="1" class="hidden" /><label for="star1" onclick="setRating(1)" class="text-gray-300 text-4xl cursor-pointer hover:text-amber-400 transition-colors duration-150">★</label>
                    </div>
                    <p class="text-xs text-gray-400">Tu opinión nos ayuda a brindarte un mejor servicio.</p>
                </div>
            `;
            // Add CSS styling rules dynamically to handle star rating hover effects
            setupStarStyles();
            break;

        case 'contencion':
            container.innerHTML = `
                <div>
                    <h2 class="text-xl font-bold text-gray-800 mb-2">Queremos mejorar</h2>
                    <p class="text-xs text-gray-500 mb-4">Lamentamos que tu experiencia no haya sido perfecta. Cuéntanos qué falló para que la gerencia pueda solucionarlo directamente.</p>
                    <textarea id="feedback-text" class="w-full border border-gray-200 rounded-2xl p-4 h-32 mb-4 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition text-sm text-gray-700" placeholder="¿Qué podemos hacer mejor? (Comida, servicio, ambiente...)"></textarea>
                    <button onclick="submitNegativeFeedback()" class="w-full bg-gradient-to-r from-red-500 to-rose-600 text-white font-semibold py-3.5 rounded-2xl hover:from-red-600 hover:to-rose-700 transition shadow-md shadow-red-100 text-sm">
                        Enviar comentario privado
                    </button>
                    <button onclick="goToStep('rating')" class="w-full mt-3 text-gray-400 text-xs py-2 hover:text-gray-600 transition">Volver atrás</button>
                </div>
            `;
            break;

        case 'tags':
            const tags = state.commerce.tags || [];
            container.innerHTML = `
                <div>
                    <h2 class="text-xl font-bold text-gray-800 mb-2">¡Qué excelente noticia!</h2>
                    <p class="text-xs text-gray-500 mb-6">¿Qué fue lo que más destacó hoy de nuestra atención? (Selecciona una o más opciones)</p>
                    
                    ${tags.length > 0 ? `
                        <div class="flex flex-wrap gap-2.5 mb-8">
                            ${tags.map(tag => `
                                <div onclick="toggleTag('${tag}')" class="px-4 py-2 border rounded-full text-xs font-semibold cursor-pointer transition-all duration-200 ${state.selectedTags.includes(tag) ? 'bg-indigo-600 border-indigo-600 text-white shadow-sm shadow-indigo-100' : 'bg-gray-50 hover:bg-gray-100 text-gray-600 border-gray-200'}">
                                    ${tag}
                                </div>
                            `).join('')}
                        </div>
                    ` : `
                        <p class="text-sm text-gray-400 italic mb-8">No hay etiquetas preestablecidas. Continuaremos con la generación.</p>
                    `}
                    
                    <button onclick="generateAiReviews()" class="w-full bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-semibold py-3.5 rounded-2xl hover:from-indigo-700 hover:to-violet-700 transition shadow-md shadow-indigo-100 disabled:opacity-50 text-sm" ${tags.length > 0 && state.selectedTags.length === 0 ? 'disabled' : ''}>
                        Generar mi reseña con IA
                    </button>
                    <button onclick="goToStep('rating')" class="w-full mt-3 text-gray-400 text-xs py-2 hover:text-gray-600 transition">Volver atrás</button>
                </div>
            `;
            break;

        case 'ai':
            container.innerHTML = `
                <div>
                    <h2 class="text-xl font-bold text-gray-800 mb-2">Elige tu reseña favorita</h2>
                    <p class="text-xs text-gray-500 mb-5">Elige la opción redactada por DeepSeek que más te guste. Se copiará al portapapeles y te abriremos Google Maps para que la pegues.</p>
                    
                    <div class="bg-amber-50 border-l-4 border-amber-500 p-3.5 mb-5 rounded-r-xl">
                        <p class="text-xs text-amber-800 leading-relaxed">
                            <strong class="font-bold">Paso 1:</strong> Selecciona una opción para copiarla.<br/>
                            <strong class="font-bold">Paso 2:</strong> En la ventana de Google Maps, mantén presionado y selecciona <strong class="underline">Pegar</strong>.
                        </p>
                    </div>
                    
                    <div class="space-y-3 mb-6 max-h-72 overflow-y-auto pr-1">
                        ${state.aiResults.map((res, i) => `
                            <div onclick="copyAndRedirect('${res.replace(/'/g, "\\'")}')" class="p-4 border border-gray-100 rounded-2xl hover:border-indigo-500 hover:bg-indigo-50/10 cursor-pointer transition duration-150 bg-gray-50/40">
                                <p class="text-xs text-gray-700 leading-relaxed italic">"${res}"</p>
                                <div class="mt-2 text-2xs text-indigo-600 font-bold flex items-center">
                                    <span>Tocar para copiar y continuar</span>
                                    <svg class="w-3.5 h-3.5 ml-1" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"></path></svg>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    <button onclick="goToStep('tags')" class="w-full text-gray-400 text-xs py-2 hover:text-gray-600 transition">Cambiar opiniones destacadas</button>
                </div>
            `;
            break;

        case 'gracias':
            container.innerHTML = `
                <div class="text-center py-6">
                    <div class="inline-flex items-center justify-center w-16 h-16 bg-emerald-100 text-emerald-500 rounded-full mb-5 text-3xl animate-bounce">✓</div>
                    <h2 class="text-2xl font-bold text-gray-800 mb-2">¡Muchas gracias!</h2>
                    <p class="text-sm text-gray-500 px-4">Tu opinión sincera y constructiva nos ayuda a mejorar y brindar la mejor atención todos los días.</p>
                </div>
            `;
            break;
    }
}

// Rating interaction
window.setRating = (val) => {
    state.rating = val;
    if (val <= 3) {
        state.step = 'contencion';
    } else {
        state.step = 'tags';
    }
    render();
};

window.goToStep = (s) => {
    state.step = s;
    render();
};

window.toggleTag = (tag) => {
    if (state.selectedTags.includes(tag)) {
        state.selectedTags = state.selectedTags.filter(t => t !== tag);
    } else {
        state.selectedTags.push(tag);
    }
    render();
};

window.submitNegativeFeedback = async () => {
    const comment = document.getElementById('feedback-text').value;
    if (!comment.trim()) return;

    state.loading = true;
    render();

    try {
        await API.submitFeedback(state.slug, state.rating, comment, []);
        state.step = 'gracias';
    } catch (e) {
        showToast(e.message || "Error al enviar el comentario");
    } finally {
        state.loading = false;
        render();
    }
};

window.generateAiReviews = async () => {
    state.loading = true;
    state.step = 'ai';
    render();

    try {
        const response = await API.generateReview(state.slug, state.selectedTags);
        state.aiResults = response.opciones;
        
        // Also register positive feedback with tags to DB for stats
        await API.submitFeedback(state.slug, state.rating, null, state.selectedTags);
    } catch (e) {
        showToast("Error al generar opiniones con IA");
        // Fallback reviews generated by UI
        state.aiResults = [
            `Excelente atención y ${state.selectedTags.join(', ').toLowerCase()}. Totalmente recomendado.`,
            `Me encantó el lugar, especialmente por ${state.selectedTags.join(', ').toLowerCase()}. Volveremos seguro.`,
            `Un sitio increíble en la zona. Destaco ${state.selectedTags.join(', ').toLowerCase()}. 10/10.`,
            `Muy buena experiencia. Destaco ${state.selectedTags.join(', ').toLowerCase()}, hicieron que valiera la pena.`,
            `Todo perfecto, desde el trato hasta ${state.selectedTags.join(', ').toLowerCase()}. Sitio de referencia.`
        ];
    } finally {
        state.loading = false;
        render();
    }
};

window.copyAndRedirect = (text) => {
    const el = document.createElement('textarea');
    el.value = text;
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
    
    showToast("¡Texto copiado al portapapeles!");
    
    setTimeout(() => {
        const placeId = state.commerce.google_place_id;
        window.open(`https://search.google.com/local/writereview?placeid=${placeId}`, '_blank');
        state.step = 'gracias';
        render();
    }, 1200);
};

// UI Toast Notification helper
function showToast(msg) {
    const box = document.createElement('div');
    box.className = "fixed bottom-5 left-1/2 -translate-x-1/2 bg-gray-900/90 text-white px-5 py-3 rounded-2xl text-center text-xs shadow-xl z-50 transition-all duration-300 transform scale-90 opacity-0";
    box.innerText = msg;
    document.body.appendChild(box);
    
    // Trigger animation
    setTimeout(() => {
        box.classList.remove('scale-90', 'opacity-0');
        box.classList.add('scale-100', 'opacity-100');
    }, 50);
    
    setTimeout(() => {
        box.classList.remove('scale-100', 'opacity-100');
        box.classList.add('scale-90', 'opacity-0');
        setTimeout(() => box.remove(), 300);
    }, 3500);
}

// CSS star rating hover hack handler
function setupStarStyles() {
    // Dynamic styles for the star rating to support hover cascading backward
    const styleId = "star-hover-styles";
    let styleEl = document.getElementById(styleId);
    if (!styleEl) {
        styleEl = document.createElement('style');
        styleEl.id = styleId;
        styleEl.innerHTML = `
            .star-rating label:hover,
            .star-rating label:hover ~ label {
                color: #fbbf24 !important;
            }
        `;
        document.head.appendChild(styleEl);
    }
}
