

set -e  

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  SMART DOCUMENT REDACTOR - PRODUCTION DEPLOYMENT        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
if ! command -v fly &> /dev/null; then
    echo " ERROR: Fly.io CLI not installed"
    echo "   Install: curl https://fly.io/install.sh | sh"
    exit 1
fi

if ! fly auth whoami &> /dev/null; then
    echo " ERROR: Not logged into Fly.io"
    echo "   Login: fly auth login"
    exit 1
fi

if ! fly secrets list | grep -q "REDIS_URL"; then
    echo "  WARNING: REDIS_URL secret not set"
    echo "   Set with: fly secrets set REDIS_URL='rediss://default:PASSWORD@YOUR_DB.upstash.io:6379?ssl_cert_reqs=CERT_REQUIRED'"
    echo ""
    read -p "Continue without REDIS_URL? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

APP_NAME=$(grep "^app = " fly.toml | cut -d '"' -f 2)
if fly apps list | grep -q "$APP_NAME"; then
    echo " App '$APP_NAME' exists - updating deployment"
else
    echo "  App '$APP_NAME' does not exist - will create new app"
    read -p "Continue? (Y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ -n $REPLY ]]; then
        exit 1
    fi
fi


echo " Deploying to Fly.io..."
echo "   App: $APP_NAME"
echo "   Region: $(grep "primary_region" fly.toml | cut -d '"' -f 2)"
echo ""

fly deploy --remote-only --build-arg PYTHONUNBUFFERED=1

echo ""
echo " Verifying deployment..."
fly status

echo ""
echo " PRODUCTION SECURITY PROPERTIES:"
echo "    Zero forensic recovery: tmpfs RAM-only storage (/tmp)"
echo "    SSL enforcement: CERT_REQUIRED for Redis connections"
echo "    Non-root execution: appuser (UID 1000)"
echo "    Automatic HTTPS: force_https = true"
echo "    Health monitoring: 30s interval checks"
echo "    Auto-healing: Failed machines replaced automatically"
echo ""
echo " Access your app at: https://$APP_NAME.fly.dev"
echo ""
echo " Monitor logs: fly logs -a $APP_NAME"
echo "   (Watch for 'tmpfs mounted' and 'CERT_REQUIRED' messages)"