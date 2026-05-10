export default function SourceSelector({ availableSources, selectedSource, onSourceChange }) {
    if (availableSources.length === 0) {
        return null;
    }

    return (
        <div className="source-selector-container">
            <span className="source-selector-label">
                Source:
            </span>
            <div className="source-selector-buttons">
                {availableSources.map(source => (
                    <button
                        key={source.name}
                        onClick={() => onSourceChange(source.name)}
                        className={`source-selector-button ${selectedSource === source.name ? 'selected' : ''}`}
                    >
                        {source.name}
                    </button>
                ))}
            </div>
        </div>
    );
}

