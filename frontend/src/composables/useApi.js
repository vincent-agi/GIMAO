// // import { ref } from "vue";
// // import api from "@/composables/http";

// // export function useApi() {
// //   const data = ref(null);
// //   const loading = ref(false);
// //   const error = ref(null);

// //   const request = async (config) => {
// //     loading.value = true;
// //     error.value = null;

// //     try {
// //       const response = await api(config);
// //       data.value = response.data;
// //       return response.data;
// //     } catch (err) {
// //       error.value = err.response?.data || err.message;
// //       throw err;
// //     } finally {
// //       loading.value = false;
// //     }
// //   };

// //   const get = (url, params = {}) =>
// //     request({ url, method: "GET", params });

// //   const post = (url, data = {}) =>
// //     request({ url, method: "POST", data });

// //   const put = (url, data = {}) =>
// //     request({ url, method: "PUT", data });

// //   const patch = (url, data = {}) =>
// //     request({ url, method: "PATCH", data });

// //   const remove = (url) =>
// //     request({ url, method: "DELETE" });

// //   return {
// //     data,
// //     loading,
// //     error,
// //     get,
// //     post,
// //     put,
// //     patch,
// //     remove,
// //   };
// // }


// import { ref } from "vue";
// import api from "@/composables/http";

// export function useApi(baseURL = null) {
//   const data = ref(null);
//   const loading = ref(false);
//   const error = ref(null);

//   const request = async (config) => {
//     loading.value = true;
//     error.value = null;
//     try {
//       const response = await api(config);
//       data.value = response.data;
//       return response.data;
//     } catch (err) {
//       error.value = err.response?.data || err.message;
//       throw err;
//     } finally {
//       loading.value = false;
//     }
//   };

//   const get = (url, params = {}) =>
//     request({ url, method: "GET", params });

//   const post = (url, data = {}) =>
//     request({ url, method: "POST", data });

//   const put = (url, data = {}) =>
//     request({ url, method: "PUT", data });

//   const patch = (url, data = {}) =>
//     request({ url, method: "PATCH", data });

//   const remove = (url) =>
//     request({ url, method: "DELETE" });

//   return {
//     data,
//     loading,
//     error,
//     get,
//     post,
//     put,
//     patch,
//     remove,
//   };
// }

import { ref } from "vue";
import api from "@/composables/http";

/**
 * Composable pour effectuer des appels à l'API REST du backend.
 *
 * Toutes les vues et composants doivent passer par ce composable pour les requêtes HTTP
 * afin de bénéficier de la gestion centralisée du token, des états de chargement et des erreurs.
 *
 * Le paramètre `baseURL` est accepté pour rétrocompatibilité mais ignoré : l'URL de base
 * est définie dans `http.js` via `axios.create({ baseURL: '/api/' })`.
 *
 * @param {string|null} baseURL - Ignoré (conservé pour compatibilité).
 * @returns {{
 *   data: import('vue').Ref<any>,
 *   loading: import('vue').Ref<boolean>,
 *   error: import('vue').Ref<string|null>,
 *   get: (url: string, params?: object) => Promise<any>,
 *   post: (url: string, data?: object) => Promise<any>,
 *   put: (url: string, data?: object) => Promise<any>,
 *   patch: (url: string, data?: object) => Promise<any>,
 *   remove: (url: string) => Promise<any>,
 *   getRaw: (url: string, params?: object, extraConfig?: object) => Promise<import('axios').AxiosResponse>
 * }}
 *
 * @example
 * const api = useApi()
 * const equipements = await api.get('equipements/', { page: 1 })
 * await api.post('demandes/', { nom: 'Panne moteur', equipement: 3 })
 *
 * @example
 * // Téléchargement de fichier : besoin des en-têtes (nom de fichier) et du blob complet,
 * // donc `getRaw` (réponse Axios entière) plutôt que `get` (qui ne retourne que `.data`).
 * const response = await api.getRaw('export/', { exportType: 'eq' }, { responseType: 'blob' })
 */
export function useApi(baseURL = null) {
  const data = ref(null);
  const loading = ref(false);
  const error = ref(null);

  const request = async (config) => {
    loading.value = true;
    error.value = null;
    try {
      const response = await api(config);
      data.value = response.data;
      return response.data;
    } catch (err) {
      error.value = err.response?.data || err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  /** @param {string} url @param {object} [params] */
  const get = (url, params = {}) =>
    request({ url, method: "GET", params });

  /** @param {string} url @param {object} [data] */
  const post = (url, data = {}) =>
    request({ url, method: "POST", data });

  /** @param {string} url @param {object} [data] */
  const put = (url, data = {}) =>
    request({ url, method: "PUT", data });

  /** @param {string} url @param {object} [data] */
  const patch = (url, data = {}) =>
    request({ url, method: "PATCH", data });

  /** @param {string} url */
  const remove = (url) =>
    request({ url, method: "DELETE" });

  /**
   * Effectue une requête GET et retourne la réponse Axios complète (headers inclus),
   * au lieu de `response.data` uniquement. Réservé aux cas où l'appelant a besoin des
   * en-têtes (ex: `content-disposition` pour un nom de fichier) ou d'un `responseType`
   * non-JSON (ex: `blob` pour un téléchargement) — sinon préférer `get`.
   *
   * @param {string} url
   * @param {object} [params]
   * @param {object} [extraConfig] - Options Axios additionnelles (ex: `{ responseType: 'blob' }`).
   * @returns {Promise<import('axios').AxiosResponse>}
   */
  const getRaw = async (url, params = {}, extraConfig = {}) => {
    loading.value = true;
    error.value = null;
    try {
      const response = await api({ url, method: "GET", params, ...extraConfig });
      data.value = response.data;
      return response;
    } catch (err) {
      error.value = err.response?.data || err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  return {
    data,
    loading,
    error,
    get,
    post,
    put,
    patch,
    remove,
    getRaw,
  };
}