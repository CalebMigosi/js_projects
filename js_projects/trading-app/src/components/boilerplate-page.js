import React, {Component} from "react";
import DashboardNavbar from "./page-elements/DashboardNavbar";
import DashboardContent from "./page-elements/DashboardContent";
import styled from "styled-components"

export default class BoilerPlatePage extends Component{
    render() {
        return (
                <Page>
                    <DashboardNavbar/>
                    <DashboardContent/>
                </Page>
            );
    }
}

const Page = styled.div`
    background-color: #050a30;
    height: 100vh;
    width: 100vw;
    display: flex;
    flex-direction: row;
    align-items: center;
`
