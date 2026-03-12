const PROTECTED_ROUTE_PREFIXES = [
	'/account',
	'/settings',
	'/admin',
	'/onboarding'
];

const GUEST_ONLY_ROUTE_PREFIXES = ['/login', '/register', '/forgot-password'];

const PUBLIC_ROUTE_PREFIXES = [
	'/',
	'/login',
	'/register',
	'/pricing',
	'/welcome',
	'/forgot-password',
	'/reset-password',
	'/auth',
	'/cgu',
	'/confidentialite',
	'/mentions-legales',
	'/privacy'
];

function matchesRoutePrefix(pathname: string, routePrefix: string) {
	return pathname === routePrefix || pathname.startsWith(`${routePrefix}/`);
}

export function isProtectedRoute(pathname: string) {
	return PROTECTED_ROUTE_PREFIXES.some((routePrefix) => matchesRoutePrefix(pathname, routePrefix));
}

export function isGuestOnlyRoute(pathname: string) {
	return GUEST_ONLY_ROUTE_PREFIXES.some((routePrefix) => matchesRoutePrefix(pathname, routePrefix));
}

export function isPublicRoute(pathname: string) {
	if (pathname === '/') return true;
	return PUBLIC_ROUTE_PREFIXES.some(
		(routePrefix) => routePrefix !== '/' && matchesRoutePrefix(pathname, routePrefix)
	);
}

export function buildLoginRedirect(pathname: string, search = '') {
	const next = `${pathname}${search}` || '/dashboard';
	return `/login?next=${encodeURIComponent(next)}`;
}
