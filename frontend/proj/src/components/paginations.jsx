export default function Pagination({ page, pages, onPageChange }) {
    if (pages <= 1)
        return null;
    return (
        <div className="pagination">
            <button className="btn btn-outline" onClick={() => onPageChange(page - 1)} disabled={page === 1}>
                ←
            </button>
            <span className="pagination-info">Page {page} of {pages}</span>
            <button className="btn btn-outline" onClick={() => onPageChange(page + 1)} disabled={page === pages}>
                →
            </button>
        </div>
    );
}