import { nextTick, onBeforeUnmount, onMounted, type Ref } from "vue";

// Llama a `onReach` cuando el centinela entra en vista dentro de `root`.
export function useInfiniteScroll(
  sentinel: Ref<HTMLElement | null>,
  root: Ref<HTMLElement | null>,
  onReach: () => boolean
) {
  let observer: IntersectionObserver | null = null;

  // Re-observar dispara el callback con el estado actual: si el centinela sigue visible, carga otra tanda.
  async function recheck() {
    await nextTick();
    if (!observer || !sentinel.value) return;
    observer.unobserve(sentinel.value);
    observer.observe(sentinel.value);
  }

  onMounted(() => {
    observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting) && onReach()) recheck();
      },
      { root: root.value, rootMargin: "200px" }
    );
    if (sentinel.value) observer.observe(sentinel.value);
  });

  onBeforeUnmount(() => observer?.disconnect());

  return { recheck };
}
