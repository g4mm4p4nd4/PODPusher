import { useState } from 'react';

export default function StarRating({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  const [hover, setHover] = useState(0);
  return (
    <div className="flex space-x-1">
      {[1, 2, 3, 4, 5].map(star => (
        <svg
          key={star}
          onMouseEnter={() => setHover(star)}
          onMouseLeave={() => setHover(0)}
          onClick={() => onChange(star)}
          data-testid={`star-${star}`}
          xmlns="http://www.w3.org/2000/svg"
          fill={(hover || value) >= star ? 'currentColor' : 'none'}
          viewBox="0 0 24 24"
          stroke="currentColor"
          className="w-6 h-6 cursor-pointer"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 17.27L18.18 21 16.54 13.97 22 9.24 14.81 8.63 12 2 9.19 8.63 2 9.24 7.46 13.97 5.82 21 12 17.27z" />
        </svg>
      ))}
    </div>
  );
}
