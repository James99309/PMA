<script setup>
defineProps({
  label: String,
  required: Boolean,
})
</script>

<template>
  <div>
    <label class="block text-xs text-gray-400 mb-1">
      {{ label }}<span v-if="required" class="text-red-400 ml-0.5">*</span>
    </label>
    <slot />
  </div>
</template>
