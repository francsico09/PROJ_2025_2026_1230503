import { useState } from 'react';
import Sidebar from './components/Sidebar.jsx';
import Topbar from './components/Topbar.jsx';
import LoginPage from './pages/login/login_page.jsx';
import DashboardPage from './pages/dashboard/individual/dashboard_individual_page.jsx';
import UsersListPage from './pages/users/list/users_list_page.jsx';
import UserEditPage from './pages/users/edit/users_edit_page.jsx';
import ProfileFormPage from "./pages/profiles/profile_form_page.jsx";
import AggregatedDashboardPage from "./pages/dashboard/aggregated/aggregated_dashboard_page.jsx";
import IndividualDashboardPage from "./pages/dashboard/individual/dashboard_individual_page.jsx";
import MetricEditFromUserPage from './pages/metrics/edit/metric_edit_from_user_page.jsx';
import MetricCreateFromUserPage from './pages/metrics/create/metric_create_from_user_page.jsx';
import ExportPage from "./pages/export/export_page.jsx";

const savedUser = (() => {
    try {
        const u = localStorage.getItem('user');
        return u ? JSON.parse(u) : null;
    } catch {
        return null;
    }
})();

export default function App() {
    const [currentUser, setCurrentUser] = useState(savedUser);
    const [page, setPage] = useState('dashboard');
    const [pageHistory, setPageHistory] = useState([]);
    const [editItem, setEditItem] = useState(null);
    const [editUser, setEditUser] = useState(null);

    const navigate = (p) => {
        setPageHistory([...pageHistory, page]);
        setPage(p);
        setEditItem(null);
    };

    const handleEdit = (p, item) => {
        setPageHistory([...pageHistory, page]);
        setPage(p);
        setEditItem(item);
    };

    const handleBack = () => {
        if (pageHistory.length > 0) {
            const newHistory = [...pageHistory];
            const previousPage = newHistory.pop();
            setPageHistory(newHistory);
            setPage(previousPage);
            setEditItem(null);
            setEditUser(null);
        }
    };

    const handleEditMetric = (metric, user) => {
        setPageHistory([...pageHistory, page]);
        setEditItem(metric);
        setEditUser(user);
        setPage('edit-metric');
    };

    const handleCreateMetric = (user) => {
        setPageHistory([...pageHistory, page]);
        setEditUser(user);
        setEditItem(null);
        setPage('create-metric');
    };

    const handleLogin = (user) => setCurrentUser(user);

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setCurrentUser(null);
        setPage('dashboard');
        setPageHistory([]);
    };

    if (!currentUser) {
        return <LoginPage onLogin={handleLogin} />;
    }

    const renderPage = () => {
        switch (page) {
            case 'aggregated-dashboard':
                return <AggregatedDashboardPage />;

            case 'individual-dashboard':
                return <IndividualDashboardPage />;

            case 'manage-users':
                return (
                    <UsersListPage
                        onEdit={(item) => handleEdit('edit-user', item)}
                        onAdd={() => navigate('create-user')}
                        onViewProfile={(data) => handleEdit('profile-form', data)}
                        onEditMetric={handleEditMetric}
                        onCreateMetric={handleCreateMetric}
                    />
                );

            case 'edit-user':
                return <UserEditPage
                    item={editItem}
                    onBack={handleBack}
                />;

            case 'create-user':
                return <UserEditPage
                    item={null}
                    onBack={() => navigate('manage-users')}
                />;

            case 'profile-form':
                return (
                    <ProfileFormPage
                        user={editItem.user}
                        profile={editItem.profile}
                        onBack={handleBack}
                    />
                );

            case 'edit-metric':
                return editItem && editUser ? (
                    <MetricEditFromUserPage
                        metric={editItem}
                        user={editUser}
                        onBack={handleBack}
                    />
                ) : null;

            case 'create-metric':
                return editUser ? (
                    <MetricCreateFromUserPage
                        user={editUser}
                        onBack={handleBack}
                    />
                ) : null;

            case 'export':
                return <ExportPage currentUser={currentUser} />;

            case 'my-user-profile':
                return <UserEditPage
                    item={currentUser}
                    onBack={handleBack}
                />;

            default:
                return <DashboardPage />;
        }
    };

    return (
        <div className="app">
            <Sidebar active={page} onNavigate={navigate} onLogout={handleLogout} user={currentUser} />
            <div className="main">
                <Topbar page={page} />
                <div className="content">{renderPage()}</div>
            </div>
        </div>
    );
}