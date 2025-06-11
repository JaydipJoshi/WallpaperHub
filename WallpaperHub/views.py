from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
import requests
from django.contrib import messages
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
import os
import time
import datetime
import uuid
from urllib.parse import urlparse
from django.utils.text import slugify
from django.urls import reverse

# Import newsletter views
from accounts.newsletter_views import newsletter_subscribe, newsletter_unsubscribe, newsletter_preferences

# Import password reset views
from accounts.password_reset_views import (
    forgot_password, forgot_password_step1, forgot_password_step2,
    forgot_password_step3, forgot_password_resend_otp, check_password_strength
)

def newsletter_test(request):
    """Test endpoint to verify URL routing"""
    print("Newsletter test endpoint called!")
    return JsonResponse({'status': 'Newsletter URL routing works!'})

key = 'I7QjbVImpvo-PQVYmkvRutei_tpEddO3HNkB__dtQ3I'

# MongoDB connection
def get_db_connection():
    """
    Get a connection to the MongoDB database
    """
    try:
        client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
        # Test the connection
        client.server_info()

        # Database will be created automatically if it doesn't exist
        db = client['wallpaperhub_db']

        # Ensure the wallpapers collection exists
        if 'wallpapers' not in db.list_collection_names():
            db.create_collection('wallpapers')
            print("Created wallpapers collection in wallpaperhub_db")

        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def get_wallpapers_collection():
    """
    Get the wallpapers collection from MongoDB
    """
    db = get_db_connection()
    if db is None:
        return None
    return db.wallpapers

def get_user_collection():
    """
    Get the users collection from MongoDB
    """
    db = get_db_connection()
    if db is None:
        return None

    # Ensure the users collection exists
    if 'users' not in db.list_collection_names():
        db.create_collection('users')
        print("Created users collection in wallpaperhub_db")

    return db.users

def landingPage(request):
    return render(request, 'landingPage.html')

def termsOfService(request):
    return render(request, 'termsOfService.html')

def privacyPolicy(request):
    return render(request, 'privacyPolicy.html')

def aboutUs(request):
    return render(request, 'aboutUs.html')

def smooth_scroll_demo(request):
    """Demo page for smooth scrolling functionality"""
    return render(request, 'smooth_scroll_demo.html')

@login_required(login_url='/login/')
def profile(request):
    """
    User profile page showing saved, uploaded, and liked wallpapers
    """
    # Get user data from MongoDB
    users = get_user_collection()
    if users is None:
        messages.error(request, 'Database error. Please try again later.')
        return redirect('userHome')

    # Find or create user document
    user_data = users.find_one({'email': request.user.email})
    print(f"Profile view - User data from MongoDB: {user_data}")

    if user_data is None:
        user_data = {
            'email': request.user.email,
            'username': request.user.username,
            'saved_wallpapers': [],
            'uploaded_wallpapers': [],
            'liked_wallpapers': []
        }
        users.insert_one(user_data)

    # Get saved wallpapers
    saved_wallpapers = []
    for wallpaper_id in user_data.get('saved_wallpapers', []):
        # Get wallpaper details from Unsplash API
        try:
            response = requests.get(f'https://api.unsplash.com/photos/{wallpaper_id}',
                                   params={'client_id': key})
            if response.status_code == 200:
                saved_wallpapers.append(response.json())
        except Exception as e:
            print(f"Error fetching saved wallpaper {wallpaper_id}: {e}")

    # Get uploaded wallpapers
    uploaded_wallpapers = []
    wallpapers_collection = get_wallpapers_collection()

    if wallpapers_collection is not None:
        # Get wallpaper IDs from user data
        for wallpaper_id in user_data.get('uploaded_wallpapers', []):
            try:
                # Get wallpaper details from MongoDB
                wallpaper = wallpapers_collection.find_one({'_id': ObjectId(wallpaper_id)})
                if wallpaper:
                    # Convert _id to string id for template compatibility
                    wallpaper['id'] = str(wallpaper['_id'])
                    uploaded_wallpapers.append(wallpaper)
            except Exception as e:
                print(f"Error fetching uploaded wallpaper {wallpaper_id}: {e}")

    # Get liked wallpapers
    liked_wallpapers = []
    for wallpaper_id in user_data.get('liked_wallpapers', []):
        # Get wallpaper details from Unsplash API
        try:
            response = requests.get(f'https://api.unsplash.com/photos/{wallpaper_id}',
                                   params={'client_id': key})
            if response.status_code == 200:
                liked_wallpapers.append(response.json())
        except Exception as e:
            print(f"Error fetching liked wallpaper {wallpaper_id}: {e}")

    import time
    context = {
        'user': request.user,
        'username': user_data.get('username', request.user.username),
        'bio': user_data.get('bio', ''),
        'profile_image': user_data.get('profile_image', None),
        'timestamp': int(time.time()),  # Add timestamp for cache busting
        'saved_wallpapers': saved_wallpapers,
        'uploaded_wallpapers': uploaded_wallpapers,
        'liked_wallpapers': liked_wallpapers
    }

    return render(request, 'profile_new.html', context)

@login_required(login_url='/login/')
def edit_profile(request):
    """
    Edit user profile information
    """
    # Get user data from MongoDB
    users = get_user_collection()
    if users is None:
        messages.error(request, 'Database error. Please try again later.')
        return redirect('profile')

    # Find user document
    user_data = users.find_one({'email': request.user.email})
    if user_data is None:
        user_data = {
            'email': request.user.email,
            'username': request.user.username,
            'bio': '',
            'saved_wallpapers': [],
            'uploaded_wallpapers': [],
            'liked_wallpapers': []
        }
        users.insert_one(user_data)

    if request.method == 'POST':
        # Update user profile
        username = request.POST.get('username', '').strip()
        bio = request.POST.get('bio', '').strip()

        # Validate username
        if not username:
            username = request.user.email.split('@')[0]  # Use part of email as default username

        # Handle profile image upload
        profile_image = None
        if 'profile_image' in request.FILES:
            image_file = request.FILES['profile_image']
            print(f"Received profile image: {image_file.name}, size: {image_file.size}, type: {image_file.content_type}")

            # Validate file size (max 2MB)
            if image_file.size > 2 * 1024 * 1024:
                messages.error(request, 'File size exceeds 2MB. Please choose a smaller image.')
                return redirect('edit_profile')

            # Validate file type
            if not image_file.content_type.startswith('image/'):
                messages.error(request, 'Please select a valid image file.')
                return redirect('edit_profile')

            # Create static/profile_images directory if it doesn't exist
            import os
            profile_images_dir = os.path.join('static', 'profile_images')
            os.makedirs(profile_images_dir, exist_ok=True)
            print(f"Profile images directory: {os.path.abspath(profile_images_dir)}")

            # Save the image with a unique filename
            filename = f"profile_{request.user.email.replace('@', '_').replace('.', '_')}_{image_file.name}"
            filepath = os.path.join(profile_images_dir, filename)
            print(f"Saving image to: {os.path.abspath(filepath)}")

            with open(filepath, 'wb+') as destination:
                for chunk in image_file.chunks():
                    destination.write(chunk)

            # Set the profile image URL
            profile_image = f"/static/profile_images/{filename}"
            print(f"Profile image URL set to: {profile_image}")

        # Prepare update data
        update_data = {'username': username, 'bio': bio}
        if profile_image:
            update_data['profile_image'] = profile_image

        print(f"Update data: {update_data}")

        # Update in MongoDB
        result = users.update_one(
            {'email': request.user.email},
            {'$set': update_data}
        )

        print(f"MongoDB update result: matched={result.matched_count}, modified={result.modified_count}")

        # Verify the update
        updated_user = users.find_one({'email': request.user.email})
        print(f"Updated user data: {updated_user}")

        # Update Django User model
        django_user = request.user

        # Check if the username is already taken by another user
        from django.contrib.auth.models import User
        if username != django_user.username and User.objects.filter(username=username).exclude(id=django_user.id).exists():
            # Username is taken, generate a unique one
            base_username = username.replace(' ', '_').lower()
            counter = 1
            unique_username = base_username

            while User.objects.filter(username=unique_username).exclude(id=django_user.id).exists():
                unique_username = f"{base_username}_{counter}"
                counter += 1

            # Use the unique username
            django_user.username = unique_username
            # Store the display name in MongoDB instead
            update_data['display_name'] = username
        else:
            # Username is available
            django_user.username = username

        django_user.save()

        # Update the accounts MongoDB collection if it exists
        try:
            from accounts.mongo_utils import get_users_collection
            accounts_users = get_users_collection()
            if accounts_users:
                accounts_users.update_one(
                    {'django_id': django_user.id},
                    {'$set': {'username': username}}
                )
        except Exception as e:
            print(f"Error updating accounts MongoDB collection: {e}")

        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    # Prepare context for GET request
    import time
    context = {
        'user': request.user,
        'username': user_data.get('display_name', user_data.get('username', request.user.username)),
        'bio': user_data.get('bio', ''),
        'profile_image': user_data.get('profile_image', None),
        'timestamp': int(time.time())  # Add timestamp for cache busting
    }

    return render(request, 'edit_profile.html', context)

@login_required(login_url='/login/')
def upload_wallpaper(request):
    """
    Handle wallpaper uploads from users
    """
    # Get user data from MongoDB
    users = get_user_collection()
    if users is None:
        messages.error(request, 'Database error. Please try again later.')
        return redirect('profile')

    # Get wallpapers collection
    wallpapers = get_wallpapers_collection()
    if wallpapers is None:
        messages.error(request, 'Database error. Please try again later.')
        return redirect('profile')

    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        tags = request.POST.get('tags', '').strip()

        # Validate form data
        if not title:
            messages.error(request, 'Please provide a title for your wallpaper.')
            return redirect('profile')

        # Handle wallpaper image upload
        if 'wallpaper_image' not in request.FILES:
            messages.error(request, 'Please select an image to upload.')
            return redirect('profile')

        image_file = request.FILES['wallpaper_image']
        print(f"Received wallpaper image: {image_file.name}, size: {image_file.size}, type: {image_file.content_type}")

        # Validate file size (max 5MB)
        if image_file.size > 5 * 1024 * 1024:
            messages.error(request, 'File size exceeds 5MB. Please choose a smaller image.')
            return redirect('profile')

        # Validate file type
        if not image_file.content_type.startswith('image/'):
            messages.error(request, 'Please select a valid image file.')
            return redirect('profile')

        # Create wallpapers directory if it doesn't exist
        import os
        import time
        import uuid
        wallpapers_dir = os.path.join('static', 'wallpapers')
        os.makedirs(wallpapers_dir, exist_ok=True)

        # Generate a unique filename
        unique_id = str(uuid.uuid4())
        timestamp = int(time.time())
        filename = f"wallpaper_{unique_id}_{timestamp}_{image_file.name}"
        filepath = os.path.join(wallpapers_dir, filename)

        # Save the image
        with open(filepath, 'wb+') as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)

        # Create wallpaper document
        wallpaper_data = {
            'title': title,
            'description': description,
            'tags': [tag.strip() for tag in tags.split(',') if tag.strip()],
            'image_path': f"/static/wallpapers/{filename}",
            'uploaded_by': request.user.email,
            'upload_date': timestamp,
            'likes': 0,
            'downloads': 0,
            'shares': 0,
            'views': 0,
            'liked_by': [],
            'custom_upload': True  # Flag to distinguish from Unsplash wallpapers
        }

        # Insert into MongoDB
        result = wallpapers.insert_one(wallpaper_data)
        wallpaper_id = str(result.inserted_id)

        # Update user's uploaded_wallpapers list
        users.update_one(
            {'email': request.user.email},
            {'$push': {'uploaded_wallpapers': wallpaper_id}}
        )

        messages.success(request, 'Wallpaper uploaded successfully!')
        return redirect('profile')

    # If GET request, just redirect to profile
    return redirect('profile')

@login_required(login_url='/login/')
def wallpaper_save(request, id):
    """
    API endpoint to save/unsave wallpapers to user profile
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    # Get request data
    try:
        data = json.loads(request.body)
        action = data.get('action', 'save')
    except:
        action = 'save'

    # Get user collection
    users = get_user_collection()
    if users is None:
        return JsonResponse({'success': False, 'error': 'Database error'}, status=500)

    # Find user document
    user_data = users.find_one({'email': request.user.email})
    if user_data is None:
        # Create new user document
        user_data = {
            'email': request.user.email,
            'username': request.user.username,
            'saved_wallpapers': [],
            'uploaded_wallpapers': [],
            'liked_wallpapers': []
        }
        users.insert_one(user_data)

    # Get saved wallpapers list
    saved_wallpapers = user_data.get('saved_wallpapers', [])

    if action == 'save':
        # Add wallpaper to saved list if not already there
        if id not in saved_wallpapers:
            saved_wallpapers.append(id)
            users.update_one(
                {'email': request.user.email},
                {'$set': {'saved_wallpapers': saved_wallpapers}}
            )
        is_saved = True
    else:  # unsave
        # Remove wallpaper from saved list
        if id in saved_wallpapers:
            saved_wallpapers.remove(id)
            users.update_one(
                {'email': request.user.email},
                {'$set': {'saved_wallpapers': saved_wallpapers}}
            )
        is_saved = False

    return JsonResponse({
        'success': True,
        'is_saved': is_saved
    })

@login_required(login_url='/login/')
def wallpaper_detail(request, id):
    """
    Display the details of a specific wallpaper
    """
    # Define params for API calls
    params = {
        "client_id": key
    }

    # First, check if this is a custom uploaded wallpaper
    try:
        # Try to parse the ID as an ObjectId
        from bson.objectid import ObjectId
        wallpapers_collection = get_wallpapers_collection()

        if wallpapers_collection is not None:
            try:
                # Try to find the wallpaper in MongoDB
                custom_wallpaper = wallpapers_collection.find_one({'_id': ObjectId(id)})

                if custom_wallpaper and custom_wallpaper.get('custom_upload'):
                    # This is a custom uploaded wallpaper
                    print(f"Found custom wallpaper: {custom_wallpaper}")

                    # Create a wallpaper object in the format expected by the template
                    wallpaper = {
                        'id': str(custom_wallpaper['_id']),
                        'urls': {
                            'full': custom_wallpaper['image_path'],
                            'regular': custom_wallpaper['image_path'],
                            'small': custom_wallpaper['image_path']
                        },
                        'alt_description': custom_wallpaper['title'],
                        'description': custom_wallpaper.get('description', ''),
                        'user': {
                            'name': custom_wallpaper['uploaded_by'],
                            'username': custom_wallpaper['uploaded_by'].split('@')[0]
                        },
                        'created_at': custom_wallpaper.get('upload_date', ''),
                        'custom_upload': True,
                        'likes': custom_wallpaper.get('likes', 0),
                        'downloads': custom_wallpaper.get('downloads', 0),
                        'shares': custom_wallpaper.get('shares', 0),
                        'views': custom_wallpaper.get('views', 0)
                    }

                    # Get or create wallpaper in MongoDB (for stats)
                    mongo_wallpaper = custom_wallpaper

                    # Skip the Unsplash API call
                    is_custom = True
                else:
                    is_custom = False
            except Exception as e:
                print(f"Error checking for custom wallpaper: {e}")
                is_custom = False
        else:
            is_custom = False
    except:
        # If the ID is not a valid ObjectId, it's an Unsplash ID
        is_custom = False

    # If not a custom wallpaper, get data from Unsplash API
    if not is_custom:
        url = f"https://api.unsplash.com/photos/{id}"
        response = requests.get(url, params=params)

        if response.status_code != 200:
            messages.error(request, "Wallpaper not found or API error")
            return redirect('user_home')

        try:
            wallpaper = response.json()

            # Check if wallpaper is a dictionary
            if not isinstance(wallpaper, dict):
                messages.error(request, "Invalid wallpaper data format received from API")
                return redirect('user_home')

            # Ensure wallpaper has all required fields
            if not wallpaper.get('id'):
                messages.error(request, "Invalid wallpaper data received from API")
                return redirect('user_home')

            # Ensure URLs dictionary exists
            if not wallpaper.get('urls') or not isinstance(wallpaper.get('urls'), dict):
                wallpaper['urls'] = {}

            # Ensure required URL fields exist
            for url_type in ['full', 'regular', 'small']:
                if url_type not in wallpaper['urls']:
                    wallpaper['urls'][url_type] = None

            # Get or create wallpaper in MongoDB
            wallpapers = get_wallpapers_collection()
            if wallpapers is None:
                # If MongoDB is not available, still show the wallpaper but without likes/downloads
                mongo_wallpaper = None
            else:
                mongo_wallpaper = wallpapers.find_one({'unsplash_id': id})
        except Exception as e:
            messages.error(request, f"Error processing wallpaper data: {e}")
            return redirect('user_home')

    # If we got here and mongo_wallpaper is not defined, it means we're using Unsplash API
    # and we need to get or create the wallpaper in MongoDB
    if not is_custom:
        if 'mongo_wallpaper' not in locals() or mongo_wallpaper is None:
            # Get or create wallpaper in MongoDB
            wallpapers = get_wallpapers_collection()
            if wallpapers is None:
                # If MongoDB is not available, still show the wallpaper but without likes/downloads
                mongo_wallpaper = None
            else:
                mongo_wallpaper = wallpapers.find_one({'unsplash_id': id})

        if mongo_wallpaper is None:
            # Create new wallpaper entry in MongoDB
            mongo_wallpaper = {
                'unsplash_id': id,
                'title': wallpaper.get('alt_description', 'Beautiful Wallpaper'),
                'likes': 0,
                'downloads': 0,
                'shares': 0,
                'views': 1,
                'liked_by': [],
                'created_at': wallpaper.get('created_at')
            }
            wallpapers.insert_one(mongo_wallpaper)
        else:
            # Increment view count
            wallpapers.update_one(
                {'unsplash_id': id},
                {'$inc': {'views': 1}}
            )
            mongo_wallpaper['views'] += 1

    # Check if user has liked this wallpaper
    is_liked = False
    is_saved = False
    if mongo_wallpaper and request.user.is_authenticated:
        is_liked = str(request.user.id) in mongo_wallpaper.get('liked_by', [])

        # Check if user has saved this wallpaper
        users = get_user_collection()
        if users is not None:
            user_data = users.find_one({'email': request.user.email})
            if user_data is not None:
                is_saved = id in user_data.get('saved_wallpapers', [])

    # Get related wallpapers
    related_wallpapers = []

    # For custom uploads, we'll try to find related wallpapers by tags
    if is_custom:
        try:
            # Get tags from the custom wallpaper
            tags = mongo_wallpaper.get('tags', [])
            if tags and wallpapers_collection is not None:
                # Find other wallpapers with similar tags
                similar_wallpapers = list(wallpapers_collection.find({'tags': {'$in': tags}, '_id': {'$ne': ObjectId(id)}, 'custom_upload': True}).limit(6))

                # Process each related wallpaper
                for wp in similar_wallpapers:
                    # Add id field for template compatibility
                    wp['id'] = str(wp['_id'])
                    related_wallpapers.append(wp)
        except Exception as e:
            print(f"Error finding related custom wallpapers: {e}")
    else:
        # For Unsplash wallpapers, use the API
        related_url = f"https://api.unsplash.com/photos/{id}/related"
        related_response = requests.get(related_url, params=params)

        if related_response.status_code == 200:
            try:
                related_data = related_response.json()

                # Handle different response formats
                if isinstance(related_data, list):
                    related_wallpapers = related_data
                elif isinstance(related_data, dict) and 'results' in related_data:
                    related_wallpapers = related_data.get('results', [])
                else:
                    related_wallpapers = []

                # Process each related wallpaper to ensure it has all required fields
                processed_related = []
                for wp in related_wallpapers:
                    # Skip if not a dictionary
                    if not isinstance(wp, dict):
                        continue

                    # Skip wallpapers without ID
                    if not wp.get('id'):
                        continue

                    # Ensure URLs dictionary exists
                    if not wp.get('urls') or not isinstance(wp.get('urls'), dict):
                        wp['urls'] = {}

                    # Ensure required URL fields exist
                    for url_type in ['full', 'regular', 'small']:
                        if url_type not in wp['urls']:
                            wp['urls'][url_type] = None

                    # Only include wallpapers with at least a small image URL
                    if wp['urls'].get('small'):
                        processed_related.append(wp)

                related_wallpapers = processed_related[:6]  # Limit to 6 related wallpapers
            except Exception as e:
                print(f"Error processing related wallpapers: {e}")

    # All related wallpaper processing is now handled in the if-else block above

    # Merge MongoDB data with Unsplash data
    if mongo_wallpaper:
        wallpaper['likes'] = mongo_wallpaper.get('likes', 0)
        wallpaper['downloads'] = mongo_wallpaper.get('downloads', 0)
        wallpaper['shares'] = mongo_wallpaper.get('shares', 0)
        wallpaper['views'] = mongo_wallpaper.get('views', 0)

    # Get the referrer URL or query parameters to preserve search context
    referrer = request.META.get('HTTP_REFERER', '')
    search_query = ''

    # Check if we're coming from another wallpaper detail page
    is_from_detail_page = '/wallpaper/' in referrer or request.GET.get('from_detail')

    # If there's a query parameter in the referrer, extract it
    if 'query=' in referrer:
        import re
        query_match = re.search(r'query=([^&]+)', referrer)
        if query_match:
            search_query = query_match.group(1)

    # If no query in referrer but one was passed directly
    if not search_query and request.GET.get('query'):
        search_query = request.GET.get('query')

    # Store the original referrer in session if coming from userHome or search results
    # This helps maintain navigation history when browsing related wallpapers
    if not is_from_detail_page and ('userHome' in referrer or search_query):
        request.session['original_referrer'] = referrer

    # Check if we're coming from another wallpaper detail page via parameter
    from_detail_id = request.GET.get('from_detail')

    # Construct the back URL
    if from_detail_id:
        # If coming from another wallpaper detail page via parameter, link back to that page
        back_url = f'/wallpaper/{from_detail_id}/'
    elif is_from_detail_page and request.session.get('original_referrer'):
        # If coming from another detail page but have original referrer in session
        back_url = request.session.get('original_referrer')
    else:
        # Default fallback
        back_url = '/userHome/'
        if search_query:
            back_url += f'?query={search_query}'

        # Update the session with this URL
        request.session['original_referrer'] = back_url

    context = {
        'wallpaper': wallpaper,
        'related_wallpapers': related_wallpapers,
        'is_liked': is_liked,
        'is_saved': is_saved,
        'back_url': back_url,
        'search_query': search_query,
        'request': request  # Pass the request object to access GET parameters in template
    }

    return render(request, 'description.html', context)

@login_required(login_url='/login/')
def wallpaper_like(request, id):
    """
    API endpoint to like/unlike a wallpaper
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        action = data.get('action', 'like')
    except json.JSONDecodeError:
        action = 'like'  # Default action

    wallpapers = get_wallpapers_collection()
    if wallpapers is None:
        return JsonResponse({'success': False, 'error': 'Database error'}, status=500)

    # Get wallpaper from MongoDB
    wallpaper = wallpapers.find_one({'unsplash_id': id})

    if wallpaper is None:
        # Create new wallpaper entry
        wallpaper = {
            'unsplash_id': id,
            'likes': 0,
            'downloads': 0,
            'views': 1,
            'liked_by': []
        }
        wallpapers.insert_one(wallpaper)

    user_id = str(request.user.id)
    liked_by = wallpaper.get('liked_by', [])

    # Get user collection to update liked wallpapers
    users = get_user_collection()
    user_email = request.user.email

    if action == 'like' and user_id not in liked_by:
        # Like the wallpaper
        wallpapers.update_one(
            {'unsplash_id': id},
            {'$inc': {'likes': 1}, '$push': {'liked_by': user_id}}
        )
        likes = wallpaper.get('likes', 0) + 1

        # Update user's liked_wallpapers array
        if users is not None:
            users.update_one(
                {'email': user_email},
                {'$addToSet': {'liked_wallpapers': id}},
                upsert=True
            )
    elif action == 'unlike' and user_id in liked_by:
        # Unlike the wallpaper
        wallpapers.update_one(
            {'unsplash_id': id},
            {'$inc': {'likes': -1}, '$pull': {'liked_by': user_id}}
        )
        likes = max(0, wallpaper.get('likes', 0) - 1)  # Ensure likes don't go below 0

        # Update user's liked_wallpapers array
        if users is not None:
            users.update_one(
                {'email': user_email},
                {'$pull': {'liked_wallpapers': id}}
            )
    else:
        # No change
        likes = wallpaper.get('likes', 0)

    return JsonResponse({
        'success': True,
        'likes': likes,
        'action': action
    })

@login_required(login_url='/login/')
def wallpaper_download(request, id):
    """
    API endpoint to track wallpaper downloads
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    wallpapers = get_wallpapers_collection()
    if wallpapers is None:
        return JsonResponse({'success': False, 'error': 'Database error'}, status=500)

    # Get wallpaper from MongoDB
    wallpaper = wallpapers.find_one({'unsplash_id': id})

    if wallpaper is None:
        # Create new wallpaper entry
        wallpaper = {
            'unsplash_id': id,
            'likes': 0,
            'downloads': 0,
            'shares': 0,
            'views': 1,
            'liked_by': []
        }
        wallpapers.insert_one(wallpaper)

    # Increment download count
    wallpapers.update_one(
        {'unsplash_id': id},
        {'$inc': {'downloads': 1}}
    )

    # Get download URL from Unsplash API
    url = f"https://api.unsplash.com/photos/{id}/download"
    params = {
        "client_id": key
    }
    response = requests.get(url, params=params)

    download_url = None
    if response.status_code == 200:
        try:
            download_data = response.json()
            if isinstance(download_data, dict):
                download_url = download_data.get('url')
        except Exception as e:
            print(f"Error parsing download URL: {e}")

    # If we couldn't get the download URL from the API, get the full image URL as fallback
    if not download_url:
        # Get the photo details to get the full image URL
        photo_url = f"https://api.unsplash.com/photos/{id}"
        photo_response = requests.get(photo_url, params=params)

        if photo_response.status_code == 200:
            try:
                photo_data = photo_response.json()
                if isinstance(photo_data, dict) and 'urls' in photo_data:
                    download_url = photo_data['urls'].get('full') or photo_data['urls'].get('raw')
            except Exception as e:
                print(f"Error getting fallback URL: {e}")

    return JsonResponse({
        'success': True,
        'downloads': wallpaper.get('downloads', 0) + 1,
        'download_url': download_url
    })

@login_required(login_url='/login/')
def wallpaper_download_file(request, id):
    """
    API endpoint to force download of a wallpaper file
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    # Get the URL from the query parameters
    url = request.GET.get('url')
    if not url:
        return JsonResponse({'success': False, 'error': 'URL parameter is required'}, status=400)

    try:
        # Get the image data
        response = requests.get(url, stream=True)

        if response.status_code != 200:
            return JsonResponse({'success': False, 'error': 'Failed to fetch image'}, status=500)

        # Determine the filename
        # Try to get the filename from the URL
        parsed_url = urlparse(url)
        path = parsed_url.path
        filename = os.path.basename(path)

        # If no filename could be determined, use a default
        if not filename or '.' not in filename:
            filename = f"wallpaper-{id}.jpg"

        # Create the response with the image data
        response_obj = HttpResponse(response.content, content_type='image/jpeg')
        response_obj['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response_obj

    except Exception as e:
        print(f"Error downloading file: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required(login_url='/login/')
def wallpaper_share(request, id):
    """
    API endpoint to track wallpaper shares
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    wallpapers = get_wallpapers_collection()
    if wallpapers is None:
        return JsonResponse({'success': False, 'error': 'Database error'}, status=500)

    # Get wallpaper from MongoDB
    wallpaper = wallpapers.find_one({'unsplash_id': id})

    if wallpaper is None:
        # Create new wallpaper entry
        wallpaper = {
            'unsplash_id': id,
            'likes': 0,
            'downloads': 0,
            'shares': 1,
            'views': 1,
            'liked_by': []
        }
        wallpapers.insert_one(wallpaper)
        shares = 1
    else:
        # Increment share count
        wallpapers.update_one(
            {'unsplash_id': id},
            {'$inc': {'shares': 1}}
        )
        shares = wallpaper.get('shares', 0) + 1

    return JsonResponse({
        'success': True,
        'shares': shares
    })


@login_required(login_url='/login/')
def userHome(request):
    query = request.GET.get("query", "")
    page = int(request.GET.get("page", 1))
    images = []
    total_pages = 0
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if query:
        url = f"https://api.unsplash.com/search/photos"
        params = {
            "query": query,
            "client_id": 'I7QjbVImpvo-PQVYmkvRutei_tpEddO3HNkB__dtQ3I',
            "per_page": 20,
            "page": page
        }
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            images = data.get("results", [])
            total_pages = data.get("total_pages", 0)

    # For AJAX requests, return only the new images
    if is_ajax:
        return JsonResponse({
            'images': images,
            'has_more': page < total_pages
        })

    # For regular requests, return the full page
    return render(request, "userHome.html", {
        "images": images,
        "query": query,
        "user": request.user,
        "current_page": page,
        "has_more": page < total_pages
    })

def loginpage(request):
    # Redirect to the login view in accounts app
    return redirect('login')

def signUpPage(request):
    # Redirect to the signup view in accounts app
    return redirect('signup')

def categories(request):
    """
    Display all available categories
    """
    return render(request, "categories.html")

def category_preview(request, category):
    """
    Display a preview of wallpapers in a specific category without requiring login
    This helps attract users by showcasing the content available on the site
    """
    page = int(request.GET.get("page", 1))
    images = []
    total_pages = 0

    # Fetch images from Unsplash API
    url = f"https://api.unsplash.com/search/photos"
    params = {
        "query": category,
        "client_id": key,
        "per_page": 50,  # Show 50 images per page
        "page": page
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        images = data.get("results", [])
        total_pages = data.get("total_pages", 0)

    # Get category description based on category name
    category_descriptions = {
        'abstract': 'Abstract and geometric wallpapers with vibrant colors and shapes',
        'nature': 'Beautiful landscapes, plants, and animals from around the world',
        'city': 'Urban landscapes and cityscapes from major cities worldwide',
        'space': 'Galaxies, stars, and cosmic scenes from the universe',
        'minimal': 'Clean, simple designs with minimalist aesthetics',
        'neon': 'Vibrant neon lights and glowing designs',
        'landscape': 'Breathtaking natural landscapes and scenery',
        'sunset': 'Beautiful sunset and sunrise scenes with stunning colors',
        # Add more categories as needed
    }

    # Default description if category not found
    description = category_descriptions.get(
        category.lower(),
        f'Explore our collection of {category} wallpapers'
    )

    # Capitalize the category name for display
    display_category = category.capitalize()

    return render(request, "category_preview.html", {
        "images": images,
        "category": display_category,
        "description": description,
        "current_page": page,
        "has_more": page < total_pages
    })

@login_required(login_url='/login/')
def settings_page(request):
    """
    User settings page with account management, analytics, appearance settings, and privacy controls
    """
    # Get user data from MongoDB
    users = get_user_collection()
    if users is None:
        messages.error(request, 'Database error. Please try again later.')
        return redirect('user_home')

    # Find user document
    user_data = users.find_one({'email': request.user.email})
    if user_data is None:
        messages.error(request, 'User data not found. Please try again later.')
        return redirect('user_home')

    # Get analytics data
    analytics_data = get_user_analytics(request.user.email)

    # Prepare context
    context = {
        'user': request.user,
        'username': user_data.get('username', request.user.username),
        'email': request.user.email,
        'profile_image': user_data.get('profile_image', None),
        'timestamp': int(time.time()),  # Add timestamp for cache busting
        'analytics': analytics_data,
        'saved_count': len(user_data.get('saved_wallpapers', [])),
        'uploaded_count': len(user_data.get('uploaded_wallpapers', [])),
        'liked_count': len(user_data.get('liked_wallpapers', []))
    }

    return render(request, 'settings.html', context)

def get_user_analytics(email):
    """
    Get or create analytics data for a user
    """
    db = get_db_connection()
    if db is None:
        return {}

    # Check if analytics collection exists
    if 'user_analytics' not in db.list_collection_names():
        db.create_collection('user_analytics')

    analytics = db.user_analytics

    # Find or create user analytics
    user_analytics = analytics.find_one({'email': email})

    if user_analytics is None:
        # Create default analytics data
        default_analytics = {
            'email': email,
            'time_spent': {
                'total_minutes': 0,
                'weekly_data': [0, 0, 0, 0, 0, 0, 0]  # Sun, Mon, Tue, Wed, Thu, Fri, Sat
            },
            'categories': {
                'abstract': 0,
                'nature': 0,
                'city': 0,
                'space': 0,
                'minimal': 0,
                'neon': 0,
                'landscape': 0,
                'sunset': 0,
                'other': 0
            },
            'downloads': {
                'total': 0,
                'monthly_data': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # Jan to Dec
            },
            'last_updated': datetime.datetime.now()
        }

        analytics.insert_one(default_analytics)
        return default_analytics

    return user_analytics
