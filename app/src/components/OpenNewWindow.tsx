import { useEffect } from 'react';

export function OpenNewWindow({
  link,
  label,
}: {
  link: string;
  label: string;
}) {
  useEffect(() => {
    window.open(link, '_blank', 'noopener,noreferrrer');
  }, [link]);

  return (
    <div>
      Opening <a href={link}>{label}</a>
    </div>
  );
}
