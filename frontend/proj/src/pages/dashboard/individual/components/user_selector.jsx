import { useState } from 'react';
import { useUsers } from '../../../../hooks/use_users.js';

export default function UserSelector({ selectedUserId, onUserSelect }) {
    const { users, loading } = useUsers();
    const [searchTerm, setSearchTerm] = useState('');
    const [isOpen, setIsOpen] = useState(false);

    // Filter only users with researcher profiles
    const researchers = users.filter(user => user.researcherProfile);

    const filteredUsers = researchers.filter(user =>
        user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const selectedUser = researchers.find(user => user.id === selectedUserId);

    return (
        <div className="user-selector-wrapper">
            <div className="user-selector-label">
                <span className="user-selector-label-text">
                    Viewing dashboard for:
                </span>
            </div>

            <div className="user-selector-container-relative">
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className="user-selector-button"
                >
                    <span>
                        {selectedUser ? `${selectedUser.name} (${selectedUser.email})` : 'Select a researcher...'}
                    </span>
                    <span className={`user-selector-button-arrow ${isOpen ? 'open' : ''}`}>
                        ▼
                    </span>
                </button>

                {isOpen && (
                    <div className="user-selector-dropdown">
                        {/* Search input */}
                        <div className="user-selector-search">
                            <input
                                type="text"
                                placeholder="Search researchers..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>

                        {/* User list */}
                        {loading ? (
                            <div className="user-selector-empty">
                                Loading researchers...
                            </div>
                        ) : filteredUsers.length === 0 ? (
                            <div className="user-selector-empty">
                                No researchers found
                            </div>
                        ) : (
                            filteredUsers.map(user => (
                                <button
                                    key={user.id}
                                    onClick={() => {
                                        onUserSelect(user.id);
                                        setIsOpen(false);
                                        setSearchTerm('');
                                    }}
                                    className={`user-selector-item ${selectedUserId === user.id ? 'selected' : ''}`}
                                >
                                    <div className="user-selector-avatar">
                                        {user.name.slice(0, 2).toUpperCase()}
                                    </div>
                                    <div className="user-selector-info">
                                        <div className="user-selector-name">{user.name}</div>
                                        <div className="user-selector-email">{user.email}</div>
                                    </div>
                                </button>
                            ))
                        )}
                    </div>
                )}
            </div>

            {/* Click outside to close */}
            {isOpen && (
                <div
                    className="user-selector-backdrop"
                    onClick={() => setIsOpen(false)}
                />
            )}
        </div>
    );
}
