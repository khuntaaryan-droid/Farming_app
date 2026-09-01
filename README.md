# Agri Shop 🌾🛒

Agri Shop is a comprehensive digital marketplace designed to bridge the gap between farmers, consumers, and agro-dealers. The platform empowers farmers to sell their fresh produce directly to consumers, while also providing them with a dedicated marketplace to purchase agricultural inputs (fertilizers, pesticides, seeds) from verified Agro Dealers.

## 🌟 Key Features

### For Farmers 🧑‍🌾
- **Direct Selling:** List and sell fresh vegetables, fruits, and grains directly to consumers and businesses.
- **Agro Store:** Purchase fertilizers, medicines, and seeds from registered Agro Dealers.
- **AI Crop Doctor:** Upload photos of diseased crops to receive instant AI-powered diagnosis and treatment recommendations (Powered by Google Gemini AI).
- **Kisan Live:** Broadcast live streams directly from the farm to showcase produce to potential buyers.
- **Kisan Forum:** Community discussion board to interact with other farmers and share knowledge.
- **Order Management:** Track sales, update order statuses (Confirmed, Shipped, Delivered), and manage transport requests.
- **Weather & Insights:** Real-time local weather tracking and market demand insights.

### For Consumers & Business Buyers 🛒
- **Shop Fresh Produce:** Browse and buy fresh produce directly from local farmers.
- **Custom Baskets:** Build customized weekly subscription baskets.
- **Negotiation:** Propose price negotiations for bulk orders.
- **Farm Map & Visits:** View farm locations on a map and book on-site farm visits.
- **Secure Payments:** Multiple payment options including Cash on Delivery (COD) and Online Payments via Razorpay.

### For Agro Dealers 🏭
- **Store Dashboard:** Manage inventory of agricultural inputs.
- **Order Fulfillment:** Receive and process orders placed by farmers for medicines and equipment.

## 🛠️ Technology Stack
- **Backend:** Python, Django 6.1
- **Database:** SQLite (Development)
- **Frontend:** HTML, CSS, Bootstrap 5 (Bootswatch Minty Theme), JavaScript
- **Integrations:** Razorpay (Payments), Google Gemini AI (Crop Diagnosis)

## 🚀 Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/khuntaaryan-droid/Farming_app.git
   cd "Farming_app"
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install django razorpay google-genai pillow
   ```

4. **Environment Variables:**
   You will need to configure the following environment variables (or update `settings.py` for local testing):
   - `GEMINI_API_KEY`: Your Google Gemini API Key for the AI Crop Doctor.
   - `RAZORPAY_KEY_ID`: Your Razorpay Key ID.
   - `RAZORPAY_KEY_SECRET`: Your Razorpay Key Secret.

5. **Run Migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Start the Development Server:**
   ```bash
   python manage.py runserver
   ```
   Access the application at `http://127.0.0.1:8000/`.

## 🔒 Security Note
Ensure that API keys and sensitive credentials are never committed to version control. Always use environment variables in production environments.
