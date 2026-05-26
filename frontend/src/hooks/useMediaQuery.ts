import { useState, useEffect } from 'react';

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia(query).matches;
    }
    // Fallback if matchMedia is not available (e.g. testing environments)
    if (typeof window !== 'undefined') {
      // Basic mock evaluation based on window width for simple testing query cases
      if (query.includes('max-width: 768px')) {
        return window.innerWidth <= 768;
      }
      if (query.includes('min-width: 769px') && query.includes('max-width: 1024px')) {
        return window.innerWidth >= 769 && window.innerWidth <= 1024;
      }
      if (query.includes('min-width: 1025px')) {
        return window.innerWidth >= 1025;
      }
    }
    return false;
  });

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) {
      // Fallback fallback for when window width changes under testing
      const handleResize = () => {
        if (query.includes('max-width: 768px')) {
          setMatches(window.innerWidth <= 768);
        } else if (query.includes('min-width: 769px') && query.includes('max-width: 1024px')) {
          setMatches(window.innerWidth >= 769 && window.innerWidth <= 1024);
        } else if (query.includes('min-width: 1025px')) {
          setMatches(window.innerWidth >= 1025);
        }
      };
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    }

    const media = window.matchMedia(query);
    setMatches(media.matches);

    const listener = (e: MediaQueryListEvent) => setMatches(e.matches);
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, [query]);

  return matches;
}

export function useIsMobile(): boolean {
  return useMediaQuery('(max-width: 768px)');
}

export function useIsTablet(): boolean {
  return useMediaQuery('(min-width: 769px) and (max-width: 1024px)');
}

export function useIsDesktop(): boolean {
  return useMediaQuery('(min-width: 1025px)');
}
