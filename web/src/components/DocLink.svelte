<script>
  // The link that opens a document: a syllabus at /resources, or CS2023 at ACM.
  import { documentHref } from '../lib/api-client.js';
  import Icon from './Icon.svelte';

  let { document, text = undefined } = $props();
  const href = $derived(documentHref(document.locator));
</script>

{#if href}
  <a class="doc" {href} target="_blank" rel="noopener">
    <Icon name="document" size={14} />
    <span>{text ?? document.name_es}</span>
    <Icon name="external" size={12} />
    <span class="sr-only">(abre el documento en una pestaña nueva)</span>
  </a>
{:else}
  <span class="doc missing"><Icon name="document" size={14} /><span>{document.name_es}</span></span>
{/if}

<style>
  .doc {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    max-width: 100%;
    min-height: 28px;
    padding: 0 10px;
    border: 1px solid color-mix(in oklch, var(--c-resource) 50%, transparent);
    border-radius: var(--radius-small);
    color: var(--text);
    font-weight: 600;
    text-decoration: none;
    transition: background 160ms, border-color 160ms;
  }

  a.doc:hover {
    background: color-mix(in oklch, var(--c-resource) 16%, transparent);
    border-color: var(--c-resource);
  }

  .doc span:not(.sr-only) {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .missing {
    border-style: dashed;
    color: var(--text-2);
    font-weight: 400;
  }
</style>
