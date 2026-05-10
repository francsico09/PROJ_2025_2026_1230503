/**
 * Badge — coloured pill label.
 * variant maps to CSS class .badge-{variant}
 */
export default function Badge({ children, variant }) {
    return (
        <span className={`badge badge-${variant}`}>
      {children}
    </span>
    );
}