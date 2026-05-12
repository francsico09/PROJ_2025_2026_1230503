export default function Searchbar({ value, onChange, placeholder = 'Search…' }) {
    return (
        <input
            className="form-input"
            value={value}
            onChange={e => onChange(e.target.value)}
            placeholder={placeholder}
        />
    );
}