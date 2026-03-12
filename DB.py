
import streamlit as st
import sqlite3
import pandas as pd
conn = sqlite3.connect('Airport Managment System.db')
cursor = conn.cursor()

st.title("✈️ Airline Dashboard & Ticket Booking")

menu = ["Dashboard", "Book Ticket"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Dashboard":
    st.subheader("Flight Dashboard")
    query = """
    SELECT f.flightID, f.flightNumber, f.origin, f.destination, f.departureTime, f.arrivalTime, f.status,
           COUNT(s.seatID) as totalSeats,
           SUM(CASE WHEN b.bookingStatus='Confirmed' THEN 1 ELSE 0 END) as bookedSeats
    FROM Flight f
    JOIN seat s ON f.AircraftID = s.AircraftID
    LEFT JOIN Booking b ON s.seatID = b.seatID
    GROUP BY f.flightID
    """
    df = pd.read_sql_query(query, conn)

    df['availableSeats'] = df['totalSeats'] - df['bookedSeats'].fillna(0)

    st.dataframe(df[['flightNumber','origin','destination','departureTime','arrivalTime','status','bookedSeats','availableSeats']])
   
    cancelled = df[df['status']=='Cancelled']
    if not cancelled.empty:
        st.warning(f"{len(cancelled)} flight(s) have been cancelled.")
    
    full = df[df['availableSeats']==0]
    if not full.empty:
        st.info(f"{len(full)} flight(s) are fully booked.")

elif choice == "Book Ticket":
    st.subheader("Book a Flight Ticket")

    flights = pd.read_sql_query("""
        SELECT f.flightID, f.flightNumber, f.origin, f.destination, f.departureTime,
               s.seatID, s.seatNumber, s.class
        FROM Flight f
        JOIN seat s ON f.AircraftID = s.AircraftID
        LEFT JOIN Booking b ON s.seatID = b.seatID AND b.bookingStatus='Confirmed'
        WHERE b.bookingID IS NULL AND f.status != 'Cancelled'
    """, conn)

    if flights.empty:
        st.write("There are no flights available")
    else:
    
        origin = st.selectbox("Origin", flights['origin'].unique())
        destination = st.selectbox("Destination", flights['destination'].unique())
        filtered = flights[(flights['origin']==origin) & (flights['destination']==destination)]

        if filtered.empty:
            st.write("NO Travlel for this destninat")
        else:
         
            filtered['price'] = filtered['class'].apply(lambda x: 500 if x=='Economy' else 1500)

            st.dataframe(filtered[['flightNumber','departureTime','seatNumber','class','price']])

            
            flight_choice = st.selectbox("Select Seat (seatID)", filtered['seatID'])

           
            passenger_name = st.text_input("Passenger Name")
            passport = st.text_input("Passport Number")
            phone = st.text_input("Phone Number")
            email = st.text_input("Email")

            if st.button("Confirm Booking"):
             
                cursor.execute("""
                INSERT INTO Passenger (passengerName, passportNumber, phoneNumber, email)
                VALUES (?, ?, ?, ?)
                """, (passenger_name, passport, phone, email))
                passengerID = cursor.lastrowid

                flightID = filtered[filtered['seatID']==flight_choice]['flightID'].values[0]
                cursor.execute("""
                INSERT INTO Booking (passengerID, flightID, seatID, bookingDate, bookingStatus)
                VALUES (?, ?, ?, datetime('now'), 'Confirmed')
                """, (passengerID, flightID, flight_choice))

                price = filtered[filtered['seatID']==flight_choice]['price'].values[0]
                cursor.execute("""
                INSERT INTO payment (bookingID, amount, paymentDate, paymentMethod, paymentStatus)
                VALUES (?, ?, datetime('now'), 'Credit Card', 'Paid')
                """, (cursor.lastrowid, price))

                conn.commit()
                st.success(f"Booking confirmed! Amount paid: ${price}")