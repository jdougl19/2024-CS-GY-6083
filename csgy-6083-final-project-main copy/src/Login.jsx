import React, {useState} from "react";

export const Login = (props) => {
    const [email, setEmail] = useState('');
    const [pass, setPass] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        console.log(email);
    }
    return(
        <div className="auth-form-container">
            <h2>Login</h2>
            <form className="login-form" onSubmit={handleSubmit}>
                <label htmlFor="email">Email</label>
                <input defaultValue={email} type="email" placeholder="Email" id="email" name="email"/>
                <label htmlFor="password">Password</label>
                <input defaultValue={pass} type="password" placeholder="Password" id="password" name="password"/>
                <button type="submit">Log In</button>
            </form>
            <button className="link-button" onClick={() => {props.onFormSwitch('register')}}>Are you new? Register here</button>
        </div>
    )
    
}