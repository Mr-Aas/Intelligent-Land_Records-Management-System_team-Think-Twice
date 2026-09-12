import React, { useState, useEffect, useRef } from 'react';
import { Bell, User, Settings, LogOut, X, Menu, Shield } from 'lucide-react';

const Navbar = () => {
    const [user, setUser] = useState(null);
    const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
    const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);
    const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
    const [isProfileDropdownOpen, setIsProfileDropdownOpen] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    const [notifications, setNotifications] = useState([
        { id: 1, text: 'Land record updated for Plot #402', read: false },
        { id: 2, text: 'Your GIS map export is ready', read: false },
        { id: 3, text: 'System maintenance scheduled for tonight', read: true },
    ]);

    const profileRef = useRef(null);
    const notificationRef = useRef(null);

    // Load user from localStorage on mount
    useEffect(() => {
        const savedUser = localStorage.getItem('bhuHarmonyUser');
        if (savedUser) {
            setUser(JSON.parse(savedUser));
        }
    }, []);

    // Handle clicks outside dropdowns
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (profileRef.current && !profileRef.current.contains(event.target)) {
                setIsProfileDropdownOpen(false);
            }
            if (notificationRef.current && !notificationRef.current.contains(event.target)) {
                setIsNotificationsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Handle Escape key to close modals/dropdowns
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'Escape') {
                setIsLoginModalOpen(false);
                setIsLogoutModalOpen(false);
                setIsProfileDropdownOpen(false);
                setIsNotificationsOpen(false);
            }
        };
        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, []);

    const handleLogin = (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const name = formData.get('name');
        const email = formData.get('email');
        const password = formData.get('password');

        if (name && email && password) {
            const newUser = { name, email };
            setUser(newUser);
            localStorage.setItem('bhuHarmonyUser', JSON.stringify(newUser));
            setIsLoginModalOpen(false);
        }
    };

    const handleLogout = () => {
        setUser(null);
        localStorage.removeItem('bhuHarmonyUser');
        setIsLogoutModalOpen(false);
        setIsProfileDropdownOpen(false);
        setIsMobileMenuOpen(false);
    };

    const markAllAsRead = () => {
        setNotifications(notifications.map((n) => ({ ...n, read: true })));
    };

    const hasUnread = notifications.some((n) => !n.read);

    const getInitials = (name) => {
        return name
            .split(' ')
            .map((n) => n[0])
            .join('')
            .toUpperCase()
            .substring(0, 2);
    };

    return (
        <>
            <nav className="fixed top-0 left-0 z-50 h-16 w-full bg-[#8ecae6] border-b border-[#74b9d6] shadow-sm flex items-center justify-between px-4 md:px-8">


                {/* Left Side: Logo & Branding */}

                <div className="flex items-center gap-3">
                    <img
                        src="/icons/Satyalogo.png"
                        alt="Government Logo"
                        className=" w-12 h-15 flex "
                    />

                    <div className="flex flex-col">
                        <h1 className="text-sm md:text-lg font-bold text-[#083344] leading-tight">
                            Land Record Management System
                        </h1>

                        <p className="text-xs md:text-sm text-[#155e75] font-medium">
                            Uttar Pradesh Government Portal
                        </p>
                    </div>
                </div>


                {/* Right Side: Desktop Navigation */}
                <div className="hidden md:flex items-center gap-6">
                    {/* Notifications */}
                    <div className="relative" ref={notificationRef}>
                        <button
                            onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
                            className="p-2 rounded-full hover:bg-gray-100 transition-colors relative focus:outline-none focus:ring-2 focus:ring-blue-500"
                            aria-label="Notifications"
                        >
                            <Bell size={20} className="text-gray-600" />
                            {hasUnread && (
                                <span className="absolute top-2 right-2.5 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
                            )}
                        </button>

                        {/* Notification Dropdown */}
                        {isNotificationsOpen && (
                            <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-100 overflow-hidden z-50">
                                <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-gray-50">
                                    <h3 className="text-sm font-semibold text-gray-800">Notifications</h3>
                                    {hasUnread && (
                                        <button
                                            onClick={markAllAsRead}
                                            className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                                        >
                                            Mark all as read
                                        </button>
                                    )}
                                </div>
                                <div className="max-h-64 overflow-y-auto">
                                    {notifications.length > 0 ? (
                                        notifications.map((notification) => (
                                            <div
                                                key={notification.id}
                                                className={`px-4 py-3 border-b border-gray-50 text-sm ${!notification.read ? 'bg-blue-50/50 text-gray-900' : 'text-gray-600'
                                                    }`}
                                            >
                                                {notification.text}
                                            </div>
                                        ))
                                    ) : (
                                        <div className="px-4 py-3 text-sm text-gray-500 text-center">
                                            No new notifications
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* User Auth Section */}
                    {!user ? (
                        <button
                            onClick={() => setIsLoginModalOpen(true)}
                            className="bg-gray-100 hover:bg-gray-200 text-gray-800 text-sm font-semibold py-2 px-5 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400"
                        >
                            LOGIN
                        </button>
                    ) : (
                        <div className="relative" ref={profileRef}>
                            <button
                                onClick={() => setIsProfileDropdownOpen(!isProfileDropdownOpen)}
                                className="flex items-center gap-3 p-1 pr-3 rounded-full hover:bg-gray-50 transition-colors border border-transparent hover:border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <div className="w-9 h-9 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold shadow-sm">
                                    {getInitials(user.name)}
                                </div>
                                <div className="flex flex-col text-left">
                                    <span className="text-sm font-semibold text-gray-900 leading-none">
                                        {user.name}
                                    </span>
                                    <span className="text-[10px] font-bold text-gray-500 tracking-wider mt-1">
                                        USER
                                    </span>
                                </div>
                            </button>

                            {/* Profile Dropdown */}
                            {isProfileDropdownOpen && (
                                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-100 py-1 z-50">
                                    <button className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 text-left">
                                        <User size={16} /> Profile
                                    </button>
                                    <button className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 text-left">
                                        <Settings size={16} /> Settings
                                    </button>
                                    <div className="h-px bg-gray-100 my-1"></div>
                                    <button
                                        onClick={() => {
                                            setIsProfileDropdownOpen(false);
                                            setIsLogoutModalOpen(true);
                                        }}
                                        className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 text-left"
                                    >
                                        <LogOut size={16} /> Logout
                                    </button>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Mobile Menu Toggle */}
                <div className="md:hidden flex items-center gap-2">
                    {user && (
                        <button
                            onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
                            className="p-2 rounded-full hover:bg-gray-100 relative"
                        >
                            <Bell size={20} className="text-gray-600" />
                            {hasUnread && (
                                <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full"></span>
                            )}
                        </button>
                    )}
                    <button
                        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                        className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg focus:outline-none"
                    >
                        {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
                    </button>
                </div>
            </nav >

            {/* Mobile Menu Dropdown */}
            {
                isMobileMenuOpen && (
                    <div className="md:hidden absolute top-16 left-0 w-full bg-white border-b border-gray-200 shadow-md z-30">
                        <div className="p-4 flex flex-col gap-4">
                            {!user ? (
                                <button
                                    onClick={() => {
                                        setIsMobileMenuOpen(false);
                                        setIsLoginModalOpen(true);
                                    }}
                                    className="w-full bg-gray-100 hover:bg-gray-200 text-gray-800 text-sm font-semibold py-3 px-5 rounded-lg transition-colors"
                                >
                                    LOGIN
                                </button>
                            ) : (
                                <>
                                    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                                        <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                                            {getInitials(user.name)}
                                        </div>
                                        <div className="flex flex-col">
                                            <span className="text-sm font-semibold text-gray-900">{user.name}</span>
                                            <span className="text-xs font-medium text-gray-500">USER</span>
                                        </div>
                                    </div>
                                    <div className="flex flex-col gap-1">
                                        <button className="flex items-center gap-3 p-3 text-sm text-gray-700 hover:bg-gray-50 rounded-lg">
                                            <User size={18} /> Profile
                                        </button>
                                        <button className="flex items-center gap-3 p-3 text-sm text-gray-700 hover:bg-gray-50 rounded-lg">
                                            <Settings size={18} /> Settings
                                        </button>
                                        <button
                                            onClick={() => {
                                                setIsMobileMenuOpen(false);
                                                setIsLogoutModalOpen(true);
                                            }}
                                            className="flex items-center gap-3 p-3 text-sm text-red-600 hover:bg-red-50 rounded-lg"
                                        >
                                            <LogOut size={18} /> Logout
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                )
            }

            {/* Login Modal */}
            {
                isLoginModalOpen && (
                    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
                        <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
                            <div className="flex justify-between items-center p-5 border-b border-gray-100">
                                <h2 className="text-xl font-bold text-gray-900">Sign In</h2>
                                <button
                                    onClick={() => setIsLoginModalOpen(false)}
                                    className="text-gray-400 hover:text-gray-600 focus:outline-none"
                                >
                                    <X size={20} />
                                </button>
                            </div>
                            <form onSubmit={handleLogin} className="p-6 flex flex-col gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                                    <input
                                        type="text"
                                        name="name"
                                        required
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                                        placeholder="e.g. Rahul Sharma"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                                    <input
                                        type="email"
                                        name="email"
                                        required
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                                        placeholder="name@example.com"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                                    <input
                                        type="password"
                                        name="password"
                                        required
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                                        placeholder="••••••••"
                                    />
                                </div>
                                <button
                                    type="submit"
                                    className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 rounded-lg transition-colors focus:ring-4 focus:ring-blue-200"
                                >
                                    Login to Portal
                                </button>
                            </form>
                        </div>
                    </div>
                )
            }

            {/* Logout Confirmation Modal */}
            {
                isLogoutModalOpen && (
                    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
                        <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm p-6 text-center animate-in fade-in zoom-in duration-200">
                            <div className="w-12 h-12 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
                                <LogOut size={24} />
                            </div>
                            <h2 className="text-lg font-bold text-gray-900 mb-2">Confirm Logout</h2>
                            <p className="text-sm text-gray-500 mb-6">
                                Are you sure you want to end your session and log out of the portal?
                            </p>
                            <div className="flex gap-3">
                                <button
                                    onClick={() => setIsLogoutModalOpen(false)}
                                    className="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium rounded-lg transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleLogout}
                                    className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors"
                                >
                                    Logout
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }
        </>
    );
};

export default Navbar;