from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Cart, Orders, Address, Payment
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.contrib import messages
from .forms import AddressForm
import razorpay
import random
from django.conf import settings
from django.core.mail import send_mail
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView


# Create your views here.
def index(request):
    allproducts = Product.objects.all()
    context = {"allproducts": allproducts}
    return render(request, "index.html", context)


class ProductRegister(CreateView):
    model = Product
    fields = "__all__"
    success_url = "/"


# class ProductList(ListView):
#     model = Product
#     queryset = Product.objects.filter(userid=id)

def ProductList(request):
    if request.user.is_authenticated:
        user= request.user
        object_list=Product.objects.filter(userid=user)
        context = {"object_list": object_list, "username":user}
        return render(request, "app/product_list.html", context)
    else:
        user = None
        return redirect("/signin")


class ProductUpdate(UpdateView):
    model = Product
    template_name_suffix = "_update_form"
    fields = "__all__"
    success_url = "/ProductList"


class ProductDelete(DeleteView):
    model = Product
    success_url = "/ProductList"


def validate_password(password):
    # Check minimum length
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")

    # Check maximum length
    if len(password) > 128:
        raise ValidationError("Password cannot exceed 128 characters.")

    # Initialize flags for character checks
    has_upper = False
    has_lower = False
    has_digit = False
    has_special = False
    special_characters = "@$!%*?&"

    # Check for character variety
    for char in password:
        if char.isupper():
            has_upper = True
        elif char.islower():
            has_lower = True
        elif char.isdigit():
            has_digit = True
        elif char in special_characters:
            has_special = True

    if not has_upper:
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not has_lower:
        raise ValidationError("Password must contain at least one lowercase letter.")
    if not has_digit:
        raise ValidationError("Password must contain at least one digit.")
    if not has_special:
        raise ValidationError(
            "Password must contain at least one special character (e.g., @$!%*?&)."
        )

    # Check against common passwords
    common_passwords = [
        "password",
        "123456",
        "qwerty",
        "abc123",
    ]  # Add more common passwords
    if password in common_passwords:
        raise ValidationError("This password is too common. Please choose another one.")


def signup(request):
    if request.method == "POST":
        uname = request.POST["uname"]
        email = request.POST["email"]
        upass = request.POST["upass"]
        ucpass = request.POST["ucpass"]
        context = {}
        try:
            validate_password(upass)
        except ValidationError as e:
            context["errmsg"] = str(e)
            return render(request, "signup.html", context)

        if uname == "" or email == "" or upass == "" or ucpass == "":
            context["errmsg"] = "Field can't be empty"
            return render(request, "signup.html", context)
        elif upass != ucpass:
            context["errmsg"] = "Password and confirm password doesn't match"
            return render(request, "signup.html", context)
        elif uname.isdigit():
            context["errmsg"] = "Username cannot consist solely of numbers."
            return render(request, "signup.html", context)
        else:
            try:
                userdata = User.objects.create(
                    username=uname, email=email, password=upass
                )
                userdata.set_password(upass)
                userdata.save()
                return redirect("/signin")
            except:
                context["errmsg"] = "User Already exists"
                return render(request, "signup.html", context)
    else:
        context = {}
        context["errmsg"] = ""
        return render(request, "signup.html", context)


def signin(request):
    if request.method == "POST":
        email = request.POST["email"]
        upass = request.POST["upass"]
        context = {}
        if email == "" or upass == "":
            context["errmsg"] = "Field can't be empty"
            return render(request, "signin.html", context)
        else:
            try:
                user = User.objects.get(email=email)  # Retrieve user by email
                userdata = authenticate(username=user.username, password=upass)
                print(userdata)
                if userdata is not None:
                    login(request, userdata)
                    return redirect("/")
                else:
                    context["errmsg"] = "Invalid username and password"
                    return render(request, "signin.html", context)
            except:
                context["errmsg"] = "User doesn't exist"
                return render(request, "signin.html", context)

    else:
        return render(request, "signin.html")


def userlogout(request):
    logout(request)
    return redirect("/")


def request_password_reset(request):
    if request.method == "POST":
        email = request.POST.get("email")
        context = {}

        # Check if the email exists
        try:
            user = User.objects.get(email=email)
            # Redirect to the password reset page
            return redirect("reset_password", username=user.username)
        except User.DoesNotExist:
            context["errmsg"] = "No account found with that email."
            return render(request, "request_password_reset.html", context)

    return render(request, "request_password_reset.html")


def reset_password(request, username):
    try:
        user = User.objects.get(username=username)

        if request.method == "POST":
            new_password = request.POST.get("new_password")
            try:
                validate_password(new_password)
                user.set_password(new_password)  # Hash the password
                user.save()
                messages.success(request, "Your password has been reset successfully.")
                return redirect(
                    "signin"
                )  # Redirect to the signin page after successful reset

            except ValidationError as e:
                messages.error(request, str(e))  # Show the validation error message
                return render(
                    request, "reset_password.html", {"username": username}
                )  # Stay on the same page

        return render(request, "reset_password.html", {"username": username})

    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("request_password_reset")


# working
def fashionlist(request):
    allproducts = Product.productmanager.fashion_list()
    context = {"allproducts": allproducts}
    return render(request, "index.html", context)


def electronicslist(request):
    allproducts = Product.productmanager.electronics_list()
    context = {"allproducts": allproducts}
    return render(request, "index.html", context)


def mobilelist(request):
    allproducts = Product.productmanager.mobile_list()
    context = {"allproducts": allproducts}
    return render(request, "index.html", context)


def grocerylist(request):
    allproducts = Product.productmanager.grocery_list()
    context = {"allproducts": allproducts}
    return render(request, "index.html", context)


def clothlist(request):
    allproducts = Product.productmanager.cloth_list()
    context = {"allproducts": allproducts}
    return render(request, "index.html", context)


def shoeslist(request):
    allproducts = Product.productmanager.shoes_list()
    context = {"allproducts": allproducts}
    return render(request, "index.html", context)


def furniturelist(request):
    allproducts = Product.productmanager.furniture_list()
    context = {"allproducts": allproducts}
    return render(request, "index.html", context)


def searchproduct(request):
    query = request.GET.get("q")
    errmsg = ""
    if query:
        allproducts = Product.objects.filter(
            Q(productname__icontains=query)
            | Q(category__icontains=query)
            | Q(description__icontains=query)
        )
        if len(allproducts) == 0:
            errmsg = "No result found!!"
    else:
        allproducts = Product.objects.all()

    context = {"allproducts": allproducts, "errmsg": errmsg}
    return render(request, "index.html", context)


def showpricerange(request):
    if request.method == "GET":
        return render(request, "index.html")
    else:
        r1 = request.POST["min"]
        r2 = request.POST.get("max")
        if r1 is not None and r2 is not None and r1.isdigit() and r2.isdigit():
            allproducts = Product.objects.filter(price__range=(r1, r2))
            print(allproducts)
            context = {"allproducts": allproducts}
            return render(request, "index.html", context)
        else:
            allproducts = Product.objects.all()
            context = {"allproducts": allproducts}
            return render(request, "index.html", context)


def sortingbyprice(request):
    sortoption = request.GET.get("sort")
    if sortoption == "low_to_high":
        allproducts = Product.objects.order_by("price")  # asc order
    elif sortoption == "high_to_low":
        allproducts = Product.objects.order_by("-price")  # desc order
    else:
        allproducts = Product.objects.all()

    context = {"allproducts": allproducts}
    return render(request, "index.html", context)


def showcarts(request):
    user = request.user
    allcarts = Cart.objects.filter(userid=user.id)
    totalamount = 0

    for x in allcarts:
        totalamount += x.productid.price * x.qty

    totalitems = len(allcarts)
    # totalitems = len(allcarts)

    if request.user.is_authenticated:
        context = {
            "allcarts": allcarts,
            "username": user,
            "totalamount": totalamount,
            "totalitems": totalitems,
        }
    else:
        context = {
            "allcarts": allcarts,
            "totalamount": totalamount,
            "totalitems": totalitems,
        }

    return render(request, "showcarts.html", context)


def addtocart(request, productid):
    if request.user.is_authenticated:
        user = request.user
    else:
        user = None

    allproducts = get_object_or_404(Product, productid=productid)
    cartitem, created = Cart.objects.get_or_create(productid=allproducts, userid=user)
    if not created:
        cartitem.qty += 1
    else:
        cartitem.qty = 1

    cartitem.save()
    return redirect("/showcarts")


def removecart(request, productid):
    user = request.user
    cartitems = Cart.objects.get(productid=productid, userid=user.id)
    cartitems.delete()
    return redirect("/showcarts")


def updateqty(request, qv, productid):
    allcarts = Cart.objects.filter(productid=productid)
    if qv == 1:
        total = allcarts[0].qty + 1
        allcarts.update(qty=total)
    else:
        if allcarts[0].qty > 1:
            total = allcarts[0].qty - 1
            allcarts.update(qty=total)
        else:
            allcarts = Cart.objects.filter(productid=productid)
            allcarts.delete()

    return redirect("/showcarts")


def addaddress(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            form = AddressForm(request.POST)
            if form.is_valid():
                address = form.save(commit=False)
                address.userid = request.user
                address.save()
                return redirect("/showaddress")
        else:
            form = AddressForm()

        context = {"form": form}
        return render(request, "addaddress.html", context)
    else:
        return redirect("/signin")


def showaddress(request):
    if request.user.is_authenticated:
        addresses = Address.objects.filter(userid=request.user)
        if request.method == "POST":
            return redirect("/make_payment")

        context = {"addresses": addresses}
        return render(request, "showaddress.html", context)
    else:
        return redirect("/signin")


def make_payment(req):
    if req.user.is_authenticated:
        cart_items = Cart.objects.filter(userid=req.user.id)
        total_amount = sum(item.productid.price * item.qty for item in cart_items)
        user = req.user
        client = razorpay.Client(
            auth=("rzp_test_wH0ggQnd7iT3nB", "eZseshY3oSsz2fcHZkTiSlCm")
        )
        try:
            data = {
                "amount": int(total_amount * 100),
                "currency": "INR",
                "receipt": str(random.randrange(1000, 90000)),
            }
            payment = client.order.create(data=data)

            for item in cart_items:
                order_id = random.randrange(1000, 90000)
                orderdata = Orders.objects.create(
                    orderid=order_id,
                    productid=item.productid,
                    userid=user,
                    qty=item.qty,
                )

                orderdata.save()
                Payment.objects.create(
                    receiptid=order_id,
                    orderid=orderdata,
                    userid=user,
                    productid=item.productid,
                    totalprice=item.qty * item.productid.price,
                )
            cart_items.delete()

            # subject = f"Flipkart payment staus for your order = {order_id}"
            # message = f"Hi {user}, Thank you for using our service \n Total Amount Paid = Rs. {total_amount}"
            # emailfrom = settings.EMAIL_HOST_USER
            # receiver = [user, user.email]
            # send_mail(subject, message, emailfrom, receiver)

            context = {"data": payment, "amount": total_amount}
            return render(req, "make_payment.html", context)
        except:
            context = {}
            context["errmsg"] = (
                "An error occurred while creating payment order. Please try again"
            )
            return render(req, "make_payment.html", context)
    else:
        return redirect("/signin")


def showorders(request):
    if request.user.is_authenticated:
        userorders = Orders.objects.filter(userid=request.user).select_related(
            "productid"
        )
        return render(request, "showorders.html", {"orders": userorders})
    else:
        return redirect("/signin")
