import Link from 'next/link';

export default function NotFound() {
  return (
    <main className="grid min-h-screen place-items-center px-6 text-center">
      <div>
        <h1 className="text-[15px] font-semibold text-neutral-900">That page is not in the showroom.</h1>
        <Link href="/" className="mt-3 inline-block rounded-full bg-neutral-900 px-5 py-2 text-[13px] font-medium text-white">
          Back to all models
        </Link>
      </div>
    </main>
  );
}
