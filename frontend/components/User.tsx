"use client";
import { useEffect, useState } from "react";
import api from "../lib/api";
import { he } from "../constants/he";

export default function UsersPage() {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    api.get("/users/2")
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
