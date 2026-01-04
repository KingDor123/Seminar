"use client";
import { useEffect, useState } from "react";
import axios from "axios";
import { he } from "../constants/he";

export default function UsersPage() {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    axios.get("http://localhost:5001/api/users/2")
      .then(res => setUsers(res.data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div>
      <h1>{he.labels.usersHeading}:</h1>
      <pre>{JSON.stringify(users, null, 2)}</pre>
    </div>
  );
}
