
import matplotlib
matplotlib.use('Agg')
import base64
import io
import tempfile
from plotly.io import to_image
from .forms import EditProfileForm
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from io import BytesIO
import plotly.io as pio
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import login as auth_login
from django.contrib.auth import get_user_model, logout, authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import PasswordResetView
from .models import Portfolio, Profile
from .forms import CustomUserCreationForm 
import httpx
from django.http import HttpResponse
from django.conf import settings
import json
from .models import DataFile, DownloadLog, Insight
from django.core.exceptions import ValidationError
import os
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd
from django.contrib.auth.forms import PasswordChangeForm
   

def home(request):
    return render(request, 'home.html')


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save(request.user)  # Save the changes to the user's profile and password if provided
            return redirect('upload')  # Redirect to profile page after saving
    else:
        form = EditProfileForm(instance=request.user)  # Pre-fill form with current user data

    return render(request, 'edit_profile.html', {'form': form})

def chat_with_gpt(request):
    # Retrieve chat history from session or initialize it
    chat_history = request.session.get('chat_history', [])

    if request.method == 'POST':
        user_input = request.POST.get('user_input', '').strip()

        # Validate user input length
        if len(user_input) > 500:
            return render(request, 'chat.html', {
                'error': "Your input is too long. Please shorten it.",
                'user_input': user_input,
                'chat_history': chat_history
            })

        # Groq API configuration
        api_key = settings.GROQ_API_KEY
        model = settings.GROQ_MODEL

        # Set system message dynamically based on user input
        if "sales" in user_input.lower():
            system_message = "Provide insights and analysis specifically about the 'sales' column."
        elif "predict" in user_input.lower():
            system_message = "Based on the historical data, predict the sales for the next quarter."
        elif "trends" in user_input.lower() or "data" in user_input.lower():
            system_message = "Analyze the dataset to identify key trends and correlations."
        elif "visualization" in user_input.lower():
            system_message = "Generate visualizations to present data insights."
        elif "portfolio" in user_input.lower():
            system_message = "List and display previous analyses or insights."
        else:
            system_message = "Analyze the dataset and provide general insights."

        # Add user message to chat history
        chat_history.append({"role": "user", "content": user_input})

        # Prepare data for the API request
        data = {
            "messages": [
                {"role": "system", "content": system_message}, 
                {"role": "user", "content": user_input}
            ],
            "model": model,
            "temperature": 0.8,
            "max_tokens": 1024,
            "top_p": 1
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Make a synchronous API request (no async)
        try:
            response = httpx.post(
                'https://api.groq.com/openai/v1/chat/completions',
                json=data,
                headers=headers
            )

            if response.status_code == 200:
                try:
                    gpt_response = response.json().get('choices', [{}])[0].get('message', {}).get('content', '')

                    # Add GPT response to chat history
                    chat_history.append({"role": "assistant", "content": gpt_response})

                     # Save the user input (prompt) and GPT response (response) in the Insight model
                    Insight.objects.create(
                        prompt=user_input,
                        response=gpt_response
                    )


                    # Update session with updated chat history
                    request.session['chat_history'] = chat_history

                    return render(request, 'chat.html', {
                        'gpt_response': gpt_response,
                        'user_input': user_input,
                        'chat_history': chat_history,
                        
                    })
                except json.JSONDecodeError:
                    return render(request, 'chat.html', {
                        'error': "Invalid JSON response from API.",
                        'user_input': user_input,
                        'chat_history': chat_history,
                         
                    })
            else:
                return render(request, 'chat.html', {
                    'error': f"API Error: {response.status_code} - {response.text}",
                    'user_input': user_input,
                    'chat_history': chat_history,
                    
                })

        except httpx.RequestError as e:
            return render(request, 'chat.html', {
                'error': f"Request error: {str(e)}",
                'user_input': user_input,
                'chat_history': chat_history,
                
            })

    # For GET requests, render the chat page
    return render(request, 'chat.html', {
        'chat_history': chat_history,
         
        
    })

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)  # Custom form for user creation

        if form.is_valid():
            user = form.save()  # Save user to the database

            # Optional: If you have a custom Profile model
            profile = Profile(user=user)
            profile.save()

            auth_login(request, user)  # Automatically login the user

            # Success message
            messages.success(request, "User registered successfully!")  # This will be handled by AJAX
            
            # Instead of redirecting, return a JSON response for AJAX
            return JsonResponse({
                'status': 'success',
                'message': 'User registered successfully!'
            })

        else:
            # Error handling for form validation errors
            errors = []
            for field, field_errors in form.errors.items():
                for error in field_errors:
                    errors.append(f"{field.capitalize()}: {error}")

            # Return error messages in JSON format
            return JsonResponse({
                'status': 'error',
                'message': errors
            })

    else:
        form = CustomUserCreationForm()

    # Always render the form (whether POST or GET)
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Authenticate the user
            user = authenticate(request, username=username, password=password)

            if user is not None:
                # Successful login
                auth_login(request, user)
                return JsonResponse({
                    'status': 'success',
                    'message': 'Login successful!'
                })
            else:
                # Check if the user exists in the database
                if User.objects.filter(username=username).exists():
                    # Password is incorrect for the existing user
                    return JsonResponse({
                        'status': 'invalid_password',
                        'message': 'Invalid password'
                    })
                else:
                    # Username does not exist
                    return JsonResponse({
                        'status': 'user_not_found',
                        'message': 'User not found'
                    })

        else:
            # If the form is not valid (e.g., missing fields or wrong data)
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid form submission. Please check your fields.'
            })

    else:
        # For GET requests, just render the login page with the form
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})

class CustomPasswordResetView(PasswordResetView):
    template_name = '  password_reset_form.html'
    email_template_name = 'password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')
    subject_template_name = 'password_reset_subject.txt'

    # Customizing the email sending logic
    def form_valid(self, form):
        email = form.cleaned_data['email']
        # Check if the email exists in your system
        send_mail(
            'Password Reset Request',
            'You requested a password reset. Click the link below to reset your password.',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return super().form_valid(form)
    
@login_required
def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        print(f"Received file: {file.name}, Size: {file.size}")

        # 1. Validate file size (10 MB limit)
        if file.size > 10 * 1024 * 1024:
            messages.error(request, "File size exceeds 10 MB limit.")
            print("File size exceeds 10 MB limit.")
            return redirect('upload')

        # 2. Validate file extension and MIME type (only CSV files)
        if not file.name.endswith('.csv') or file.content_type not in ['text/csv', 'application/vnd.ms-excel']:
            messages.error(request, "Only valid CSV files are allowed.")
            print("Invalid file extension or MIME type.")
            return redirect('upload')

        # 3. Save the file to the database
        try:
            new_file = DataFile(user=request.user, file=file)
            new_file.save()
            messages.success(request, "File uploaded successfully.")
            print("File uploaded successfully.")
        except Exception as e:
            messages.error(request, f"Error uploading file: {str(e)}")
            print(f"Error during file upload: {e}")
            return redirect('upload')

        # 4. Process the CSV file
        file_path = new_file.file.path
        try:
            # Read CSV with error handling for bad lines
            df = pd.read_csv(file_path, on_bad_lines='warn')
            print(f"File read successfully: {df.shape[0]} rows and {df.shape[1]} columns.")

            # Data Cleaning
            df.dropna(inplace=True)  # Remove rows with missing values
            df.drop_duplicates(inplace=True)  # Remove duplicate rows

            # Clean string columns
            for column in df.select_dtypes(include=['object']).columns:
                df[column] = df[column].str.strip()

            # Validate numeric columns
            for column in df.select_dtypes(include=['number']).columns:
                df[column] = pd.to_numeric(df[column], errors='coerce')

            # Final cleanup for invalid numeric data
            df.dropna(inplace=True)
            print(f"Data cleaned: {df.shape[0]} rows remaining.")

            # Convert cleaned data to JSON for visualization
            chart_data = df.to_dict(orient='records')
            request.session['chart_data'] = chart_data  # Store in session for dynamic charts

            # Redirect to static view
            return redirect('static_view', file_id=new_file.id)

        except Exception as e:
            messages.error(request, f"Error processing CSV file: {str(e)}")
            print(f"Error during file processing: {e}")
            return redirect('upload')

    return render(request, 'upload.html')


@login_required
def static_view(request, file_id):
    # Fetch the uploaded file
    data_file = get_object_or_404(DataFile, id=file_id)

    try:
        # Read the CSV file
        file_path = data_file.file.path
        df = pd.read_csv(file_path, sep=None, engine='python', on_bad_lines='skip')  # Auto-detect delimiter

        # Log successful file read
        print(f"File read successfully: {df.shape[0]} rows and {df.shape[1]} columns")

    except Exception as e:
        messages.error(request, f"Error reading CSV file: {str(e)}")
        print(f"Error reading CSV file: {e}")
        return redirect('upload')

    # Generate preview table (first 20 rows)
    table_html = df.head(20).to_html(classes='table table-striped table-bordered')

    # Get available columns
    available_columns = df.columns.tolist()
    if len(available_columns) < 2:
        messages.error(request, "The file must have at least two columns for visualization.")
        return redirect('upload')

    # Get selected X and Y axes from the request, default to the first two columns
    x_axis = request.GET.get('x_axis', available_columns[0])
    y_axis = request.GET.get('y_axis', available_columns[1])

    # Validate the selected columns
    if x_axis not in available_columns or y_axis not in available_columns:
        messages.error(request, "Invalid column selection for visualization.")
        x_axis = available_columns[0]  # Default to the first column
        y_axis = available_columns[1]  # Default to the second column

     # Initialize chart JSONs and alert messages
    chart_render_status = {
        'scatter': False,
        'line': False,
        'area': False,
        'radar': False,
        'bar': False,
        'pie': False,
        'stacked_bar': False,
        'grouped_bar': False,
        'heatmap': False,
        'boxplot': False,
        'histogram': False,
    }
    # Initialize chart JSONs
    scatter_chart_json = bar_chart_json = line_chart_json = pie_chart_json = stacked_bar_chart_json = grouped_bar_chart_json = None
    histogram_chart_json = boxplot_chart_json = heatmap_chart_json = None
    area_chart_json = radar_chart_json =  None

    try:
        # Case 1: Both axes are numeric
        if pd.api.types.is_numeric_dtype(df[x_axis]) and pd.api.types.is_numeric_dtype(df[y_axis]):
            # Render all charts
            scatter_fig = px.scatter(df, x=x_axis, y=y_axis)
            scatter_chart_json = scatter_fig.to_json()
            chart_render_status['scatter'] = True

            bar_fig = px.bar(df, x=x_axis, y=y_axis)
            bar_chart_json = bar_fig.to_json()
            chart_render_status['bar'] = True

            line_fig = px.line(df, x=x_axis, y=y_axis)
            line_chart_json = line_fig.to_json()
            chart_render_status['line'] = True

            pie_fig = px.pie(df, names=x_axis, values=y_axis)
            pie_chart_json = pie_fig.to_json()
            chart_render_status['pie'] = True

            histogram_fig = px.histogram(df, x=x_axis)
            histogram_chart_json = histogram_fig.to_json()
            chart_render_status['histogram'] = True

            boxplot_fig = px.box(df, x=x_axis, y=y_axis)
            boxplot_chart_json = boxplot_fig.to_json()
            chart_render_status['boxplot'] = True

            area_fig = px.area(df, x=x_axis, y=y_axis)
            area_chart_json = area_fig.to_json()
            chart_render_status['area'] = True


            radar_fig = px.line_polar(df, r=y_axis, theta=x_axis)
            radar_chart_json = radar_fig.to_json()
            chart_render_status['radar'] = True

        # Case 2: One axis is numeric, and the other is categorical
        elif (pd.api.types.is_numeric_dtype(df[x_axis]) and pd.api.types.is_object_dtype(df[y_axis])) or \
             (pd.api.types.is_object_dtype(df[x_axis]) and pd.api.types.is_numeric_dtype(df[y_axis])):
            # Render charts like scatter, line, area, radar, bar, and pie
            scatter_fig = px.scatter(df, x=x_axis, y=y_axis)
            scatter_chart_json = scatter_fig.to_json()
            chart_render_status['scatter'] = True

            line_fig = px.line(df, x=x_axis, y=y_axis)
            line_chart_json = line_fig.to_json()
            chart_render_status['line'] = True

            area_fig = px.area(df, x=x_axis, y=y_axis)
            area_chart_json = area_fig.to_json()
            chart_render_status['area'] = True

            radar_fig = px.line_polar(df, r=y_axis, theta=x_axis)
            radar_chart_json = radar_fig.to_json()
            chart_render_status['radar'] = True

            bar_fig = px.bar(df, x=x_axis, y=y_axis)
            bar_chart_json = bar_fig.to_json()
            chart_render_status['bar'] = True

            pie_fig = px.pie(df, names=x_axis, values=y_axis)
            pie_chart_json = pie_fig.to_json()
            chart_render_status['pie'] = True

        # Stacked Bar Chart: This is usually for comparing multiple categories over a categorical axis
            if pd.api.types.is_object_dtype(df[x_axis]) and pd.api.types.is_numeric_dtype(df[y_axis]):
                stacked_bar_fig = px.bar(df, x=x_axis, y=y_axis, color=x_axis, title=f"Stacked Bar Chart for {x_axis} vs {y_axis}")
                stacked_bar_chart_json = stacked_bar_fig.to_json()
                chart_render_status['stacked_bar'] = True

            # Grouped Bar Chart: If we have one categorical and one numeric axis, grouped by another categorical axis
            if pd.api.types.is_object_dtype(df[x_axis]) and pd.api.types.is_numeric_dtype(df[y_axis]):
                grouped_bar_fig = px.bar(df, x=x_axis, y=y_axis, color=y_axis, barmode='group', title=f"Grouped Bar Chart for {x_axis} vs {y_axis}")
                grouped_bar_chart_json = grouped_bar_fig.to_json()
                chart_render_status['grouped_bar'] = True

            # Heatmap: This is typically used for categorical vs categorical data, but we can show it if needed
            if pd.api.types.is_object_dtype(df[x_axis]) and pd.api.types.is_object_dtype(df[y_axis]):
                heatmap_data = pd.crosstab(df[x_axis], df[y_axis])
                if not heatmap_data.empty:
                    heatmap_fig = px.imshow(heatmap_data, text_auto=True, title=f"Heatmap of {x_axis} vs {y_axis}")
                    heatmap_chart_json = heatmap_fig.to_json()
                    chart_render_status['heatmap'] = True
                else:
                    heatmap_chart_json = None
                    messages.warning(request, f"No valid data found for heatmap between {x_axis} and {y_axis}.")

            # Boxplot: Only render if y_axis is numeric and x_axis is categorical
            if pd.api.types.is_numeric_dtype(df[y_axis]) and pd.api.types.is_object_dtype(df[x_axis]):
                boxplot_fig = px.box(df, x=x_axis, y=y_axis)
                boxplot_chart_json = boxplot_fig.to_json()
                chart_render_status['boxplot'] = True

            # Histogram: Only render if x_axis is numeric
            if pd.api.types.is_numeric_dtype(df[x_axis]):
                histogram_fig = px.histogram(df, x=x_axis)
                histogram_chart_json = histogram_fig.to_json()
                chart_render_status['histogram'] = True

            # Render appropriate message or charts for any unhandled conditions
            if scatter_chart_json is None:
                messages.warning(request, "Both axes need to be numeric for scatter, line, and box plots.")


        # Case 3: Both axes are categorical
        elif pd.api.types.is_object_dtype(df[x_axis]) and pd.api.types.is_object_dtype(df[y_axis]):
            # Render charts for categorical vs categorical data
            # Bar Chart
            bar_fig = px.bar(df, x=x_axis, y=y_axis)
            bar_chart_json = bar_fig.to_json()
            chart_render_status['bar'] = True

            # Pie Chart (x-axis only as categories)
            pie_fig = px.pie(df, names=x_axis)
            pie_chart_json = pie_fig.to_json()
            chart_render_status['pie'] = True

            # Heatmap: Cross-tabulation (counts of categorical combinations)
            heatmap_data = pd.crosstab(df[x_axis], df[y_axis])

            # Check if heatmap_data is non-empty and valid
            if not heatmap_data.empty:
                heatmap_fig = px.imshow(heatmap_data, text_auto=True, title=f"Heatmap of {x_axis} vs {y_axis}")
                heatmap_chart_json = heatmap_fig.to_json()
                chart_render_status['heatmap'] = True
            else:
                messages.warning(request, f"No valid data found for heatmap between {x_axis} and {y_axis}.")

             # Stacked Bar Chart: If y_axis is numeric, render stacked chart
            if pd.api.types.is_numeric_dtype(df[y_axis]):
                stacked_bar_fig = px.bar(df, x=x_axis, y=y_axis, color=y_axis, barmode='stack')
                stacked_bar_chart_json = stacked_bar_fig.to_json()
                chart_render_status['stacked_bar'] = True

            # Grouped Bar Chart: Both x and y are categorical, render grouped chart
            if pd.api.types.is_object_dtype(df[x_axis]) and pd.api.types.is_object_dtype(df[y_axis]):
                grouped_bar_fig = px.bar(df, x=x_axis, y=y_axis, color=y_axis, barmode='group')
                grouped_bar_chart_json = grouped_bar_fig.to_json()
                chart_render_status['grouped_bar'] = True


            # Do not render scatter, line, area, or radar charts for categorical data
            scatter_chart_json = None
            line_chart_json = None
            area_chart_json = None
            radar_chart_json = None
            histogram_chart_json = None
            boxplot_chart_json = None

        else:
            messages.warning(request, "Unrecognized data types for the selected columns.")
            
    except Exception as e:
        messages.error(request, f"Error generating visualizations: {str(e)}")
        print(f"Error generating visualizations: {e}")
        
    # Render the response
    return render(request, 'static_view.html', {
        'csv_file': data_file,
        'table_html': table_html,
        'available_columns': available_columns,
        'x_axis': x_axis,
        'y_axis': y_axis,
        'scatter_chart_json': scatter_chart_json,
        'bar_chart_json': bar_chart_json,
        'line_chart_json': line_chart_json,
        'pie_chart_json': pie_chart_json,
        'histogram_chart_json': histogram_chart_json,
        'boxplot_chart_json': boxplot_chart_json,
        'heatmap_chart_json': heatmap_chart_json,
        'area_chart_json': area_chart_json,
        'radar_chart_json': radar_chart_json,
        'stacked_bar_chart_json': stacked_bar_chart_json,
        'grouped_bar_chart_json': grouped_bar_chart_json,
        'chart_render_status': chart_render_status,
    })

from datetime import datetime
# Helper function to save Plotly chart as base64 image
def save_plotly_to_base64(fig):
    """
    Convert Plotly figure to base64 encoded PNG image.
    """
    img_data = to_image(fig, format='png')
    return base64.b64encode(img_data).decode()


def write_image_to_tempfile(image_data):
    """
    Write base64 image data to a temporary file.
    """
    image_data = base64.b64decode(image_data)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    temp_file.write(image_data)
    temp_file.close()
    return temp_file.name


# Function to generate PDF with Plotly charts
def generate_pdf(request, file_id):
    # Fetch the data file
    data_file = get_object_or_404(DataFile, id=file_id)
    
    # Load the CSV file into pandas DataFrame
    df = pd.read_csv(data_file.file.path)

    # Get the available columns for x and y axis
    available_columns = df.columns.tolist()

    # Get the selected columns from the query parameters (or use defaults if not provided)
    x_col = request.GET.get('x_axis', available_columns[0])  # Default to the first column if not selected
    y_col = request.GET.get('y_axis', available_columns[1])  # Default to the second column if not selected

    # Validate the selected columns
    if x_col not in available_columns or y_col not in available_columns:
        raise ValueError("Invalid column selected for x or y axis")

    # Generate Plotly charts as base64 images
    charts = {}

    scatter_fig = px.scatter(df, x=x_col, y=y_col, title=f"Scatter Plot ({x_col} vs {y_col})", hover_data=df.columns)
    charts['scatter'] = save_plotly_to_base64(scatter_fig)

    bar_fig = px.bar(df, x=x_col, y=y_col, title=f"Bar Chart ({x_col} vs {y_col})", hover_data=df.columns)
    charts['bar'] = save_plotly_to_base64(bar_fig)

    line_fig = px.line(df, x=x_col, y=y_col, title=f"Line Chart ({x_col} vs {y_col})", hover_data=df.columns)
    charts['line'] = save_plotly_to_base64(line_fig)

    pie_fig = px.pie(df, names=x_col, values=y_col, title=f"Pie Chart ({x_col} Distribution)")
    charts['pie'] = save_plotly_to_base64(pie_fig)

    # Add new charts: Area and Radar
    area_fig = px.area(df, x=x_col, y=y_col, title=f"Area Chart ({x_col} vs {y_col})")
    charts['area'] = save_plotly_to_base64(area_fig)

    radar_fig = px.line_polar(df, r=x_col, theta=y_col, line_close=True, title="Radar Chart")
    charts['radar'] = save_plotly_to_base64(radar_fig)

    # Add Heatmap if relevant (categorical vs categorical)
    if pd.api.types.is_object_dtype(df[x_col]) and pd.api.types.is_object_dtype(df[y_col]):
        heatmap_data = pd.crosstab(df[x_col], df[y_col])
        if not heatmap_data.empty:
            heatmap_fig = px.imshow(heatmap_data, text_auto=True, title=f"Heatmap of {x_col} vs {y_col}")
            charts['heatmap'] = save_plotly_to_base64(heatmap_fig)

    # Add Histogram if x_col is numeric
    if pd.api.types.is_numeric_dtype(df[x_col]):
        histogram_fig = px.histogram(df, x=x_col, title=f"Histogram of {x_col}")
        charts['histogram'] = save_plotly_to_base64(histogram_fig)

    # Add Boxplot if y_col is numeric and x_col is categorical
    if pd.api.types.is_numeric_dtype(df[y_col]) and pd.api.types.is_object_dtype(df[x_col]):
        boxplot_fig = px.box(df, x=x_col, y=y_col, title=f"Boxplot ({x_col} vs {y_col})")
        charts['boxplot'] = save_plotly_to_base64(boxplot_fig)

    # Add Grouped Bar Chart (if both x_col and y_col are categorical or numeric)
    if pd.api.types.is_object_dtype(df[x_col]) and pd.api.types.is_numeric_dtype(df[y_col]):
        grouped_bar_fig = px.bar(df, x=x_col, y=y_col, color=y_col, barmode='group', title=f"Grouped Bar Chart ({x_col} vs {y_col})")
        charts['grouped_bar'] = save_plotly_to_base64(grouped_bar_fig)

    # Add Stacked Bar Chart (if x_col is categorical and y_col is numeric)
    if pd.api.types.is_object_dtype(df[x_col]) and pd.api.types.is_numeric_dtype(df[y_col]):
        stacked_bar_fig = px.bar(df, x=x_col, y=y_col, color=x_col, barmode='stack', title=f"Stacked Bar Chart ({x_col} vs {y_col})")
        charts['stacked_bar'] = save_plotly_to_base64(stacked_bar_fig)

    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="file_details_{data_file.id}.pdf"'

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 10)

    # Add file details to the PDF (Centered on the first page)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(300, 700, f"File Name: {data_file.file.name}")
    
    c.setFont("Helvetica", 10)
    c.drawCentredString(300, 685, f"Uploaded By: {data_file.user.username}")
    c.drawCentredString(300, 670, f"Uploaded At: {data_file.uploaded_at}")
    c.drawCentredString(300, 655, f"Downloaded At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.line(100, 640, 500, 640)

     # Log the download in the DownloadLog model
    DownloadLog.objects.create(user=request.user, file=data_file, downloaded_at=datetime.now())

    # Add Data Visualizations heading and charts to the PDF
    c.showPage()  # Move to the next page for data visualizations
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 750, "Data Visualizations:")

    # Start adding charts immediately after the heading
    y_position = 400  # Start placing charts below the Data Visualizations heading

    for chart_name, chart_data in charts.items():
        chart_file_path = write_image_to_tempfile(chart_data)

        if y_position < 50:  # Check if we need a new page
            c.showPage()  # Create a new page
            y_position = 400  # Reset the y position for new page

        c.drawImage(chart_file_path, 100, y_position, width=400, height=300)
        y_position -= 320  # Adjust y position for the next chart

        # Remove temporary image file
        os.remove(chart_file_path)

    c.save()

    # Write the response
    response.write(buffer.getvalue())
    buffer.close()

    return response

@login_required
def view_history(request):
    # Ensure only files uploaded by the current user are being retrieved
    files = DataFile.objects.filter(user=request.user).order_by('-uploaded_at')
    
    # Add this print statement to check if files are being retrieved
    print(files)
    
    return render(request, 'view_history.html', {'files': files})


@login_required
def delete_file(request, file_id):
    # Fetch the file object
    file = get_object_or_404(DataFile, id=file_id)
    
    # Ensure the file belongs to the current user
    if file.user != request.user:
        messages.error(request, "You are not authorized to delete this file.")
        return redirect('view_history')
    
    # Delete the file
    file.delete()
    messages.success(request, "File deleted successfully.")
    return redirect('view_history')

@login_required
def view_profile(request):
    """Fetch user profile details."""
    profile = request.user.profile
    data = {
        'username': request.user.username,
        'email': request.user.email,
        'bio': profile.bio,
        'phone_number': profile.phone_number,
        'profile_picture': profile.profile_picture.url if profile.profile_picture else None
    }
    return JsonResponse(data)


@login_required
def portfolio(request):
    user = request.user

    # Fetch all the portfolios of the logged-in user
    portfolios = Portfolio.objects.filter(user=user)

    # Fetch all the files uploaded by the user
    uploaded_files = DataFile.objects.filter(user=user)

    # Fetch all the insights related to the user's files
    insights = Insight.objects.filter()

    return render(request, 'portfolio.html', {
        'user': user,
        'portfolios': portfolios,
        'uploaded_files': uploaded_files,
        'insights': insights,
    })