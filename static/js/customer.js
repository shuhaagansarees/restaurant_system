let cart = {};

// Tabs Logic
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.menu-section').forEach(s => s.classList.remove('active'));
        
        tab.classList.add('active');
        document.getElementById(tab.dataset.target).classList.add('active');
    });
});

function getVariant(itemId) {
    const radio = document.querySelector(`input[name="var_${itemId}"]:checked`);
    return radio ? radio.value : null;
}

function addToCart(btn) {
    const menuItem = btn.closest('.menu-item');
    const id = menuItem.dataset.id;
    
    btn.style.display = 'none';
    menuItem.querySelector('.stepper').classList.add('active');
    
    updateQty(menuItem.querySelector('.stepper button'), 1, true);
}

function updateQty(btn, change, fromAdd = false) {
    const menuItem = btn.closest('.menu-item');
    const id = menuItem.dataset.id;
    const name = menuItem.dataset.name;
    const price = parseFloat(menuItem.dataset.price);
    const variant = getVariant(id);
    
    // Unique key if variants matter, simplified here by ID
    const cartKey = id; 

    if (!cart[cartKey]) {
        cart[cartKey] = { id: id, name: name, price: price, quantity: 0, variant: variant };
    }
    
    if (!fromAdd) {
        cart[cartKey].quantity += change;
    } else {
        cart[cartKey].quantity = 1;
    }
    
    const qtySpan = menuItem.querySelector('.qty');
    
    if (cart[cartKey].quantity <= 0) {
        delete cart[cartKey];
        menuItem.querySelector('.stepper').classList.remove('active');
        menuItem.querySelector('.btn-add').style.display = 'block';
        qtySpan.innerText = "1"; // reset for next time
    } else {
        qtySpan.innerText = cart[cartKey].quantity;
    }
    
    updateCartUI();
}

function updateCartUI() {
    let totalItems = 0;
    let totalPrice = 0;
    
    for (let key in cart) {
        totalItems += cart[key].quantity;
        totalPrice += cart[key].quantity * cart[key].price;
    }
    
    const stickyCart = document.getElementById('sticky-cart');
    document.getElementById('cart-count').innerText = totalItems;
    document.getElementById('cart-total').innerText = totalPrice;
    
    if (totalItems > 0) {
        stickyCart.classList.add('active');
    } else {
        stickyCart.classList.remove('active');
    }
}

function openCheckout() {
    const reviewDiv = document.getElementById('cart-review');
    reviewDiv.innerHTML = '';
    for(let key in cart) {
        const item = cart[key];
        let varText = item.variant ? ` (${item.variant})` : '';
        reviewDiv.innerHTML += `<div style="display:flex; justify-content:space-between; margin-bottom:5px;">
            <span>${item.quantity}x ${item.name}${varText}</span>
            <span>₹${item.price * item.quantity}</span>
        </div>`;
    }
    document.getElementById('checkout-modal').classList.add('active');
}

function closeCheckout() {
    document.getElementById('checkout-modal').classList.remove('active');
}

async function placeOrder() {
    let finalTable = currentTable;
    let manualTableEl = document.getElementById('manual-table');
    let orderType = 'dine-in';
    
    if (!finalTable && manualTableEl) {
        finalTable = manualTableEl.value;
        if (!finalTable) {
            orderType = 'parcel';
        }
    }
    
    const custName = document.getElementById('cust-name').value;
    const custMobile = document.getElementById('cust-mobile').value;
    
    const items = Object.values(cart);
    
    const payload = {
        table_name: finalTable,
        order_type: orderType,
        customer_name: custName,
        customer_mobile: custMobile,
        items: items
    };
    
    try {
        const response = await fetch('/api/place_order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]') ? document.querySelector('meta[name="csrf-token"]').content : '' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        
        if (data.success) {
            window.location.href = `/order/${data.order_id}`;
        } else {
            alert('Error: ' + data.message);
        }
    } catch (err) {
        console.error(err);
        alert('Failed to place order.');
    }
}
