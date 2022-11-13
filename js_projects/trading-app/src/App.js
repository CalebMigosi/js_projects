import React from "react";
import {Routes, Route} from "react-router-dom";
import Home from "./pages/Home/Home"
import "./assets/styles/styles.css"

function App() {
  return (
    <Routes>
        <Route path ="/" element = {<Home />}></Route>
    </Routes>
  );
}

export default App;
