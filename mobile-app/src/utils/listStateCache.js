// In-memory list filter/search/sort cache.
// Survives a list → detail → back round-trip (vue-router unmounts the list
// component, so local refs are lost); module-singleton keeps the last query
// state per list key. Cleared on app relaunch (in-memory only) → a fresh
// launch starts unfiltered, which is the desired behaviour.

const _cache = {}

export function saveListState(key, state) {
  _cache[key] = state
}

export function loadListState(key) {
  return _cache[key] || null
}
