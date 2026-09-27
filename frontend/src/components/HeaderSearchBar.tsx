/**
 * Header search bar: find a place, jump to the planner with it set as the
 * starting point. Hidden on the planner itself (App.tsx) -- the sidebar
 * already has an Origin field there, so a second identical search box next
 * to it was pure repetition. Everywhere else (the Helene case study, the
 * methodology/about pages) it previously set context that nothing on screen
 * read; now it always does something -- take you to the planner, ready to go.
 */
import { useNavigate } from 'react-router-dom';

import LocationSearch from '@/components/LocationSearch';
import { useHeaderSearch } from '@/contexts/HeaderSearchContext';
import type { Location } from '@/types/trip';

export default function HeaderSearchBar() {
  const { searchedLocation, setSearchedLocation } = useHeaderSearch();
  const navigate = useNavigate();

  function handleChange(location: Location | null) {
    setSearchedLocation(location);
    if (location) navigate('/');
  }

  return (
    <div className="header-search">
      <LocationSearch
        id="header-search"
        label="Search a place to start planning a trip"
        value={searchedLocation}
        onChange={handleChange}
      />
    </div>
  );
}
