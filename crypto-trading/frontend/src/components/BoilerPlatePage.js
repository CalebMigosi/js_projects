import React from "react";
import DashboardNavbar from "./page-elements/DashboardNavbar";
import DashboardContent from "./page-elements/DashboardContent";
import styled from "styled-components"

export default function BoilerPlatePage(props){
    return (
            <Page>
                <DashboardNavbar/>
                <DashboardContent>
                    {props.children}
                </DashboardContent>
            </Page>
        );
}

const Page = styled.div`
    background-color: #050a30;
    height: 100vh;
    width: 100vw;
    display: flex;
    flex-direction: row;
    align-items: center;
`
