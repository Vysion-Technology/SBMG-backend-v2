#!/bin/bash

# FCM Notifications Setup Script for SBM Gramin Rajasthan

echo "🚀 Setting up FCM Notifications for SBM Gramin Rajasthan..."
echo ""

# Check if we're in the backend directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    exit 1
fi

# Step 1: Install firebase-admin
echo "📦 Step 1: Installing firebase-admin package..."
pip install firebase-admin>=6.0.0
if [ $? -eq 0 ]; then
    echo "✅ firebase-admin installed successfully"
else
    echo "❌ Failed to install firebase-admin"
    exit 1
fi
echo ""

# Step 2: Check for FCM credentials
echo "🔑 Step 2: Checking Firebase credentials..."
if [ -z "$FCM_CREDENTIAL_PATH" ]; then
    echo "⚠️  FCM_CREDENTIAL_PATH environment variable not set"
    echo ""
    echo "To set up Firebase credentials:"
    echo "1. Go to Firebase Console: https://console.firebase.google.com/"
    echo "2. Select your project or create a new one"
    echo "3. Go to Project Settings → Service Accounts"
    echo "4. Click 'Generate new private key'"
    echo "5. Save the JSON file securely"
    echo "6. Set the environment variable:"
    echo "   export FCM_CREDENTIAL_PATH=/path/to/your-firebase-credentials.json"
    echo ""
    read -p "Enter the path to your Firebase credentials JSON file (or press Enter to skip): " cred_path
    
    if [ ! -z "$cred_path" ]; then
        if [ -f "$cred_path" ]; then
            export FCM_CREDENTIAL_PATH="$cred_path"
            echo "✅ FCM_CREDENTIAL_PATH set to: $cred_path"
            
            # Add to .env file if it exists
            if [ -f ".env" ]; then
                if grep -q "FCM_CREDENTIAL_PATH" .env; then
                    sed -i '' "s|FCM_CREDENTIAL_PATH=.*|FCM_CREDENTIAL_PATH=$cred_path|" .env
                else
                    echo "FCM_CREDENTIAL_PATH=$cred_path" >> .env
                fi
                echo "✅ Added FCM_CREDENTIAL_PATH to .env file"
            else
                echo "FCM_CREDENTIAL_PATH=$cred_path" > .env
                echo "✅ Created .env file with FCM_CREDENTIAL_PATH"
            fi
        else
            echo "❌ File not found: $cred_path"
            echo "⚠️  Skipping FCM credentials setup. You can set it up later."
        fi
    else
        echo "⚠️  Skipping FCM credentials setup. You can set it up later."
    fi
else
    echo "✅ FCM_CREDENTIAL_PATH is set: $FCM_CREDENTIAL_PATH"
    if [ -f "$FCM_CREDENTIAL_PATH" ]; then
        echo "✅ Credentials file exists"
    else
        echo "❌ Warning: Credentials file not found at $FCM_CREDENTIAL_PATH"
    fi
fi
echo ""

# Step 3: Run database migration
echo "🗄️  Step 3: Running database migration..."
alembic upgrade head
if [ $? -eq 0 ]; then
    echo "✅ Database migration completed successfully"
else
    echo "❌ Database migration failed"
    echo "Please ensure your database is running and accessible"
    exit 1
fi
echo ""

# Step 4: Summary
echo "✅ FCM Notifications Setup Complete!"
echo ""
echo "📋 Summary:"
echo "  - firebase-admin package installed"
echo "  - Database tables created (user_device_tokens, public_user_device_tokens)"
echo "  - API endpoints available at /api/v1/notifications/"
echo ""
echo "📚 Next Steps:"
echo "  1. Ensure FCM_CREDENTIAL_PATH is set in your environment or .env file"
echo "  2. Start your FastAPI server: uvicorn main:app --reload"
echo "  3. Test device registration endpoints"
echo "  4. Integrate FCM SDK in your mobile app"
echo "  5. See FCM_NOTIFICATIONS.md for detailed documentation"
echo ""
echo "🔗 API Endpoints:"
echo "  - POST /api/v1/notifications/staff/register-device (Staff users)"
echo "  - POST /api/v1/notifications/public/register-device (Public users)"
echo "  - DELETE /api/v1/notifications/staff/remove-device/{device_id}"
echo ""
echo "📖 For more information, see: FCM_NOTIFICATIONS.md"
