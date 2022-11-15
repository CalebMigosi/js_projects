import BoilerPlatePage from "../components/BoilerPlatePage"
import React from "react"
import styled from "styled-components"
import Tabs from "../components/ui/Tabs"
import DashboardContent from "../components/page-elements/DashboardContent"
import DashboardNavbar from "../components/page-elements/DashboardNavbar"

export default function Home(){
    return (
    <BoilerPlatePage className="boiler-plate-page">
        <Tabs></Tabs>
    </BoilerPlatePage>)
}

const Test = styled.div`
    background-color: white;
    width: 500px;
    height: 200px;
    z-index: 2;
`