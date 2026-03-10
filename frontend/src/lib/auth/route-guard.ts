const PROTECTED_ROUTE_PREFIXES = [
	'/dashboard',
	'/scis',
	'/exploitation',
	'/finance',
	'/biens',
	'/associes',
	'/charges',
	'/fiscalite',
	'/locataires',
	'/loyers',
	'/account',
	'/settings',
	'/success',
	'/admin'
];

const GUEST_ONLY_ROUTE_PREFIXES = ['/login', '/register'];

function matchesRoutePrefix(pathname: string, routePrefix: string) {
	return pathname === routePrefix || pathname.startsWith(`${routePrefix}/`);
}

export function isProtectedRoute(pathname: string) {
	return PROTECTED_ROUTE_PREFIXES.some((routePrefix) => matchesRoutePrefix(pathname, routePrefix));
}

export function isGuestOnlyRoute(pathname: string) {
	return GUEST_ONLY_ROUTE_PREFIXES.some((routePrefix) => matchesRoutePrefix(pathname, routePrefix));
}

export function buildLoginRedirect(pathname: string, search = '') {
	const next = `${pathname}${search}` || '/dashboard';
	return `/login?next=${encodeURIComponent(next)}`;
}
