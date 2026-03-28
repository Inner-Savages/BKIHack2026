/**
 * Svelte stores.
 * activeCodes usunięty — stan kodów jest teraz po stronie backendu.
 * Store `lastCode` przechowuje ostatnio wygenerowany kod do przekazania
 * między Phone a Site (tylko w ramach jednej sesji przeglądarki).
 */
import { writable } from 'svelte/store';

/** Ostatnio wygenerowany kod (string 6 cyfr) — null jeśli brak */
export const lastGeneratedCode = writable(null);
