import { LoadingCardView } from '@/components/showroom/LoadingCard';

/**
 * What a car's page shows while its code comes over (moving to it from the line-up, or from another car's menu): the same
 * card the viewer takes over once it is up, so the wait reads as one.
 */
export default function ShowroomLoading() {
  return (
    <div className="fixed inset-0 grid place-items-center bg-[#f1f2f4]">
      <LoadingCardView label="Loading the showroom" detail="Opening the car" instant />
    </div>
  );
}
