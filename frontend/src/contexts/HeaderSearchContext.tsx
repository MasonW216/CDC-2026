/**
 * Lets the header's search bar (App.tsx) hand a resolved place to whichever
 * page is currently mounted below it. PlannerPage uses it to set the origin,
 * the way "jump to a place" search works before you've picked a starting
 * point any other way.
 */
import { createContext, useContext, useState } from 'react';

import type { Location } from '@/types/trip';

interface HeaderSearchContextValue {
  searchedLocation: Location | null;
  setSearchedLocation: (location: Location | null) => void;
}

const HeaderSearchContext = createContext<HeaderSearchContextValue | null>(null);

export function HeaderSearchProvider({ children }: { children: React.ReactNode }) {
  const [searchedLocation, setSearchedLocation] = useState<Location | null>(null);
  return (
    <HeaderSearchContext.Provider value={{ searchedLocation, setSearchedLocation }}>
      {children}
    </HeaderSearchContext.Provider>
  );
}

// A provider and its own hook belong together in one file.
// eslint-disable-next-line react-refresh/only-export-components
export function useHeaderSearch(): HeaderSearchContextValue {
  const context = useContext(HeaderSearchContext);
  if (!context) {
    throw new Error('useHeaderSearch must be used within a HeaderSearchProvider');
  }
  return context;
}
