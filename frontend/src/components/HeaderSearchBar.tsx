/**
 * Header search bar: find a place, use it as the trip's starting point.
 * Wraps the same LocationSearch/geocode path the planner's own Origin field
 * uses -- no separate search implementation to keep in sync.
 */
import LocationSearch from '@/components/LocationSearch';
import { useHeaderSearch } from '@/contexts/HeaderSearchContext';

export default function HeaderSearchBar() {
  const { searchedLocation, setSearchedLocation } = useHeaderSearch();
  return (
    <div className="header-search">
      <LocationSearch
        id="header-search"
        label="Search a place (sets your starting point)"
        value={searchedLocation}
        onChange={setSearchedLocation}
      />
    </div>
  );
}
