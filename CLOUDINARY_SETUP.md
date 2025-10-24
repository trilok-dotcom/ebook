# Cloudinary Setup Guide

## Step 1: Create Free Cloudinary Account

1. Go to: https://cloudinary.com/users/register_free
2. Sign up with your email (or use Google/GitHub)
3. Verify your email

## Step 2: Get Your Cloud Name

1. After logging in, go to your Dashboard: https://console.cloudinary.com/
2. You'll see your **Cloud name** at the top (e.g., `dxyz123abc`)
3. Copy this cloud name

## Step 3: Create Upload Preset

1. Go to Settings → Upload: https://console.cloudinary.com/settings/upload
2. Scroll down to **Upload presets**
3. Click **Add upload preset**
4. Configure:
   - **Preset name:** `medical_records`
   - **Signing Mode:** Select **"Unsigned"** (important!)
   - **Folder:** Leave empty (we set it dynamically in code)
   - **Access Mode:** Upload
5. Click **Save**

## Step 4: Configure Your App

1. Copy `frontend/.env.example` to `frontend/.env` (if you haven't already)
2. Edit `frontend/.env` and add your Cloudinary cloud name:

```env
VITE_CLOUDINARY_CLOUD_NAME=your_cloud_name_here
```

Replace `your_cloud_name_here` with the cloud name from Step 2.

## Step 5: Test Upload

1. Restart your frontend dev server:
   ```bash
   cd frontend
   npm run dev
   ```

2. Sign in as a doctor
3. Try uploading a medical record
4. It should now upload to Cloudinary!

## Cloudinary Free Tier Limits

- ✅ **25 GB** storage
- ✅ **25 GB** bandwidth per month
- ✅ **Unlimited** transformations
- ✅ **No credit card** required

This is more than enough for development and small production use!

## Viewing Your Uploads

Go to: https://console.cloudinary.com/console/media_library

You'll see all uploaded files organized in folders:
- `records/{doctorId}/{patientId}/`

## Security Note

The upload preset is "unsigned" which means anyone with your cloud name can upload. For production, you should:
1. Use a signed upload preset
2. Implement server-side upload signature generation
3. Add upload restrictions (file size, file types, etc.)

But for development/testing, unsigned uploads are fine!
