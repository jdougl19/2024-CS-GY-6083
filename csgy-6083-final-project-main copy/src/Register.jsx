import React, {useState} from "react";

export const Register = (props) => {
    const [email, setEmail] = useState('');
    const [pass, setPass] = useState('');
    const [fname, setFname] = useState('');
    const [lname, setLname] = useState('');
    const [street, setStreet] = useState('');
    const [city, setCity] = useState('');
    const [state, setState] = useState('');
    const [zipcode, setZipcode] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        console.log(email);
    }

    return (
        <div className="auth-form-container">
            <h2>Register</h2>
            <form className="register-form" onSubmit={handleSubmit}>
            <label htmlFor="fname">First Name</label>
            <input defaultValue={fname} type="text" placeholder="First Name" id="fname" name="fname"/>
            
            <label htmlFor="lname">Last Name</label>
            <input defaultValue={lname} type="text" placeholder="Last Name" id="lname" name="lname"/>
            
            <label htmlFor="street">Street</label>
            <input defaultValue={street} type="text" placeholder="Street Address" id="street" name="street"/>
            
            <label htmlFor="city">City</label>
            <input defaultValue={city} type="text" placeholder="City" id="city" name="city"/>
            
            <label htmlFor="state">State</label>
            <input defaultValue={state} type="text" placeholder="State" id="state" name="state"/>
            
            <label htmlFor="zipcode">Zipcode</label>
            <input defaultValue={zipcode} type="text" placeholder="Zipcode" id="zipcode" name="zipcode"/>
            
            <label htmlFor="email">Email</label>
            <input defaultValue={email} type="email" placeholder="Email" id="email" name="email"/>
            
            <label htmlFor="password">Password</label>
            <input defaultValue={pass} type="password" placeholder="Password" id="password" name="password"/>
            
            <button type="submit">Register</button>
            </form>
            <button className="link-button" onClick={() => {props.onFormSwitch('Login')}}>Already have an account? Login here</button>
        </div>
    )
}