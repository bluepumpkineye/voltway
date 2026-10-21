export async function resolve(specifier, context, nextResolve) {
  if ((specifier.startsWith('./') || specifier.startsWith('../')) && !/\.[a-z]+$/.test(specifier)) {
    try {
      return await nextResolve(specifier + '.ts', context);
    } catch {}
  }
  return nextResolve(specifier, context);
}
