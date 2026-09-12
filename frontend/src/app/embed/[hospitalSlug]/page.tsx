import { MediBookWidget } from "@/components/medibook-widget/widget-shell";

export default async function EmbedPage({
  params,
}: {
  params: Promise<{
    hospitalSlug: string;
  }>;
}) {
  const { hospitalSlug } =
    await params;

  return (
    <MediBookWidget
      hospitalSlug={hospitalSlug}
    />
  );
}
