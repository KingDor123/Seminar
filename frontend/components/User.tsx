"use client";
import { useEffect, useState } from "react";
import axios from "axios";

export default function UsersPage() {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    axios.get("http://localhost:5001/api/users/2")
      .then(res => setUsers(res.data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div>
      <h1>Users:</h1>
      <pre>{JSON.stringify(users, null, 2)}</pre>
    </div>
  );
}
